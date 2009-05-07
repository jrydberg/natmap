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

from zope.interface import implements
from natmap.inatmap import IDiscover

from twisted.plugin import IPlugin
from twisted.internet import defer, reactor
from twisted.internet.protocol import DatagramProtocol
import random
import socket



def iterrandrange(n, start, stop):
    return (random.randint(start, stop) for i in range(n))


class MulticastDiscoverProtocol(DatagramProtocol):

    def __init__(self):
        self.deferred = defer.Deferred()

    def datagramReceived(self, datagram, address):
        deferred, self.deferred = self.deferred, None
        if deferred is not None and datagram == 'ping':
            deferred.callbackk(address[0])
            self.timeout.cancel()
             
    def discover(self):
        for port in iterrandrange(5, 1024, 65535):
            try:
                self.listeningPort = reactor.listenMulticast(port, self)
            except error.CannotListenError:
                continue
            break
        else:
            raise

        self.listningPort.joinGroup('239.255.255.250', socket.INADDR_ANY)
        dst = ('239.255.255.250', self.listeningPort.getHost().port)
        self.transport.write('ping', dst)
        self.transport.write('ping', dst)
        self.transport.write('ping', dst)

        self.timeout = reactor.callLater(5, self.cancel)

        return self.deferred

    def cancel(self):
        deferred, self.deferred = self.deferred, None
        if deferred is not None:
            deferred.errback(error.TimeoutError())


class LocalNetworkMulticastDiscover(DatagramProtocol):
    """
    Mechanism for discovering the internal address by probing for a
    UPnP device.
    """
    implements(IPlugin, IDiscover)

    def discover(self):
        """
        Try to discover internal IP address.
        """
        protocol = MulticastDiscoverProtocol()
        return protocol.discover()


discover = LocalNetworkMulticastDiscover()
