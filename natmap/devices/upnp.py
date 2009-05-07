# This file is part of Nat Map.
# Copyright (c) 2009 Johan Rydberg <johan.rydberg@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# This code is based on nattraverso.

from zope.interface import implements

from twisted.internet.protocol import DatagramProtocol
from twisted.plugin import IPlugin
from twisted.internet import reactor, defer, error

from natmap.inatmap import IMappingDevice, IMappingDeviceProvider
from natmap.soap import Proxy
from natmap.xmlbuilder import Namespace
from natmap import DiscoverError, MappingGroup, discoverInternalAddress

from twisted.web import client

import random
import socket

from xml.etree.ElementTree import fromstring


# UPNP multicast address, port and request string
_UPNP_MCAST = '239.255.255.250'
_UPNP_PORT = 1900
_UPNP_SEARCH_REQUEST = """M-SEARCH * HTTP/1.1\r
Host:%s:%s\r
ST:urn:schemas-upnp-org:device:InternetGatewayDevice:1\r
Man:"ssdp:discover"\r
MX:3\r
\r
""" % (_UPNP_MCAST, _UPNP_PORT)


import urlparse

def iterrandrange(n, start, stop):
    return (random.randint(start, stop) for i in range(n))


class BadResponseError(Exception):
    pass



class UPnPMappingDevice:
    """

    @ivar serviceURL: the URL where we do requests.
    """

    def __init__(self, baseURL, controlURL):
        self.serviceURL = urlparse.urljoin(baseURL, controlURL)
        namespace = Namespace(
            "rn:schemas-upnp-org:service:WANIPConnection:1", "u"
            )
        self.proxy = Proxy(self.serviceURL, namespace)

    def createMappingGroup(self):
        """
        See L{IMappingDevice.createMappingGroup}.
        """
        return MappingGroup()

    def mapGroup(self, mappingGroup):
        """
        See L{IMappingDevice.mapGroup}.

        @rtype: L{Deferred}
        """
        mappings = {}
        def eb(reason):
            pass

        @defer.inlineCallbacks
        def map(internalAddress):
            pass

        return discoverInternalAddress().addCallback(map)

    def discoverExternalAddress(self):
        """
        See L{IMappingDevice.discoverExternalAddress}.
        """
        def cb(result):
            return result['NewExternalIPAddress']
        d = self.proxy.callRemote('GetExternalIPAddress')
        return d.addCallback(cb)


class DiscoverProtocol(DatagramProtocol):
    """
    Datagram protocol used to discover UPnP capable devices in the
    network.
    """

    def __init__(self):
        self.deferred = defer.Deferred()
        self.timeout = None
        self.controlURL = None
        self.ns = '{urn:schemas-upnp-org:device-1-0}'
        
    def search(self, timeout):
        """
        Search for stuff.
        """
        for port in iterrandrange(5, 1900, 2500):
            try:
                self.listeningPort = reactor.listenMulticast(port, self)
            except error.CannotListenError:
                continue
            break
        else:
            raise

        self.listeningPort.joinGroup(_UPNP_MCAST, socket.INADDR_ANY)
        dst = (_UPNP_MCAST, _UPNP_PORT)
        self.transport.write(_UPNP_SEARCH_REQUEST, dst)
        self.transport.write(_UPNP_SEARCH_REQUEST, dst)
        self.transport.write(_UPNP_SEARCH_REQUEST, dst)
        
        self.timeout = reactor.callLater(5, self.cancel)
        return self.deferred

    def cbDiscover(self, data):
        """
        Callback from retreiving the service information.
        """
        WANSERVICES = ['urn:schemas-upnp-org:service:WANIPConnection:1',
                       'urn:schemas-upnp-org:service:WANPPPConnection:1']

        document = fromstring(data)

        # iterate through all provided services and try to find the
        # control URL.
        for serviceElement in document.findall('.//%sservice' % self.ns):
            serviceType = serviceElement.findtext(self.ns + 'serviceType')
            if serviceType in WANSERVICES:
                self.controlURL = serviceElement.findtext(
                    self.ns + 'controlURL')
                break
        self.baseURL = document.findtext(self.ns + 'URLBase')

        if self.controlURL is not None:
            self.callback(UPnPMappingDevice(self.baseURL,
                                            self.controlURL))

        
    def datagramReceived(self, data, address):
        """
        Process incoming data.
        """
        if self.controlURL is not None:
            return None

        if self.timeout is not None:
            timeout, self.timeout = self.timeout, None
            timeout.cancel()
        
        code, headers, data = self.parseResponse(data)
        location = headers.get('location', None)
        if location is None:
            self.errback(DiscoverError())

        client.getPage(location).addCallback(
            self.cbDiscover).addErrback(self.errback)
        
    def parseResponse(self, data):
        """
        Parse HTTP response.
        
        Return a tuple of response code, dictionary of headers and the
        response content body.
        """
        firstline = True
        headers = {}

        while data:
            line, data = data.split('\r\n', 1)
            if firstline:
                
                version, code, status = line.split(' ', 2)
                if version != 'HTTP/1.1' and version != 'HTTP/1.0':
                    raise BadResponseError("bad http version")

                if code != '200':
                    raise BadResponseError("bad response code")

                firstline = False
            elif not line:
                break
            else:
                key, value = line.split(':', 1)
                headers[key.lower()] = value

        if firstline is True:
            raise BadResponeError("no response line")

        return code, headers, data

    def callback(self, result):
        """
        Call deferred callback with result.
        """
        deferred, self.deferred = self.deferred, None
        if deferred is not None:
            deferred.callback(result)
        return result
            
    def errback(self, reason):
        """
        Call deferred errback with reason.
        """
        deferred, self.deferred = self.deferred, None
        if deferred is not None:
            deferred.errback(reason)
        return reason

    def cancel(self):
        self.errback(error.TimeoutError())
        

class UPnPMappingDeviceProvider:
    """
    """
    implements(IPlugin, IMappingDeviceProvider)
    
    def search(self, timeout):
        protocol = DiscoverProtocol()
        return protocol.search(timeout)

provider = UPnPMappingDeviceProvider()

    
        
