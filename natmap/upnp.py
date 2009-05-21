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

from xml.etree.ElementTree import fromstring

from twisted.internet.protocol import DatagramProtocol
from twisted.internet.address import IPv4Address
from twisted.plugin import IPlugin
from twisted.internet import reactor, defer, error
from twisted.web import client

from natmap.inatmap import IMapper
from natmap.soap import Proxy, SOAPFault
from natmap.xmlbuilder import Namespace
from natmap.internal import discoverInternalHost

import random
import socket
import urlparse
import itertools


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


def iterrandrange(n, start, stop):
    return (random.randint(start, stop) for i in range(n))


class BadResponseError(Exception):
    pass


class Mapping:
    """
    Object representing a mapping between an internal address and an
    external address.

    @ivar internalHost: A string containing the internal IP address.
    @ivar internalPort: An integer representing the internal port
        number.
    @ivar externalPort: An integer representing the external port
        number.
    @ivar type: A string representing the type of transport, either
        'TCP' or 'UDP'
    """

    def __init__(self, type, internalHost, internalPort,
                 externalPort):
        self.type = type
        self.internalHost = internalHost
        self.internalPort = internalPort
        self.externalPort = externalPort


class UPnPMapper(object):
    """
    Implementor of L{IMapper} for the UPnP IGD.

    @ivar serviceURL: the URL where we do requests.
    """
    implements(IMapper)

    def __init__(self, proxy):
        self.proxy = proxy

    @defer.inlineCallbacks
    def getMappings(self):
        """
        Return a C{Deferred} called with a sequence of L{Mapping}
        objects that represent all currently known mappings in the
        mapping device.
        """
        mappings = list()
        for index in itertools.count():
            try:
                entry = yield self.proxy.callRemote(
                    'GetGenericPortMappingEntry', NewPortMappingIndex=index)
                mapping = Mapping(entry['NewProtocol'],
                                  entry['NewInternalClient'],
                                  entry['NewInternalPort'],
                                  entry['NewExternalPort'])
                mappings.append(mapping)
            except SOAPFault:
                break
        defer.returnValue(mappings)

    def allocateExternalPort(self, type, internalPort):
        """
        Allocate an external port for the given internal port.

        @return: a deferred called with the allocated external port.
        """
        def cb(mappings):
            external_ports = ((mapping.type, mapping.externalPort)
                              for mapping in mappings)
            for port in iterrandrange(20, 1025, 65536):
                if not (type, port) in external_ports:
                    return port
            return internalPort
        return self.getMappings().addCallback(cb)

    def _buildExternalAddress(self, addressType, externalPort):
        """
        Based on given parameters build a L{IPv4Address} object that
        represent the external endpoint.

        @return: a deferred called with the external L{IPv4Address} object
        """
        def cb(externalHost):
            return IPv4Address(addressType, externalHost, externalPort)
        return self.discoverExternalHost().addCallback(cb)

    def _addPortMapping(self, internalHost, type, internalPort, externalPort):
        """
        Add a port mapping.

        @param internalHost: IP address where mapping should be directed.
        @param type: C{UDP | TCP}
        @param internalPort: port within the NAT
        @param externalPort: port outside the NAT
        """
        if type not in ('UDP', 'TCP'):
            return defer.fail(ValueError("bad protocol"))

        description = "%s:%d (%s)" % (internalHost, internalPort, type)
        return self.proxy.callRemote(
            'AddPortMapping', NewRemoteHost=" ",
            NewExternalPort=externalPort, NewProtocol=type,
            NewInternalPort=internalPort, NewInternalClient=internalHost,
            NewEnabled=1, NewPortMappingDescription=description,
            NewLeaseDuration=0
            )

    def map(self, internalAddress):
        """
        See L{IMapper.map}.

        @rtype: L{Deferred}
        """
        def mapped(result, externalPort):
            return self._buildExternalAddress(
                internalAddress.type, externalPort
                )

        def allocated(externalPort):
            return self._addPortMapping(
                internalAddress.host, internalAddress.type,
                internalAddress.port, externalPort
                ).addCallback(mapped, externalPort)

        return self.allocateExternalPort(internalAddress.type,
                                         internalAddress.port).addCallback(
            allocated)


    def discoverExternalHost(self):
        """
        See L{IMapper.discoverExternalHost}.
        """
        def cb(result):
            return result['NewExternalIPAddress']

        return self.proxy.callRemote('GetExternalIPAddress').addCallback(cb)


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
            serviceURL = urlparse.urljoin(self.baseURL, self.controlURL)
            namespace = Namespace(
                "urn:schemas-upnp-org:service:WANIPConnection:1", "u"
                )
            self.callback(UPnPMapper(Proxy(serviceURL, namespace)))
        
    def datagramReceived(self, data, address):
        """
        Process incoming data.
        """
        if self.controlURL is not None:
            return None

        if self.timeout is not None:
            timeout, self.timeout = self.timeout, None
            timeout.cancel()
        
        try:
            code, headers, data = self.parseResponse(data)
        except BadResponseError:
            return

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
        

def discoverMapper(timeout=5):
    """
    Discover UPnP mapper.

    @return: a deferred called with a IMapper provider.
    """
    return DiscoverProtocol().search(timeout)


    
        
