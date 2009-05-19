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

# Functionality for discovering the "internal" address (it may turn
# out to be a "real" address).

from twisted.internet import defer, reactor
from twisted.internet.protocol import DatagramProtocol
import random
import socket


def iterrandrange(n, start, stop):
    return (random.randint(start, stop) for i in range(n))


class DiscoverError(Exception):
    """
    Internal address could not be discovered.
    """


def connectedSocketDiscover():
    """
    Try to discover the internal address by using a connected UDP
    socket.

    @return: a L{Deferred} called with the internal address.
    """
    def cb(address):
        protocol = DatagramProtocol()
        listeningPort = reactor.listenUDP(0, protocol)
        protocol.transport.connect(address, 7)
        internal = protocol.transport.getHost().host
        listeningPort.stopListening()
        return internal
    return reactor.resolve('A.ROOT-SERVERS.NET').addCallback(cb)


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


def localNetworkMulticastDiscover():
    """
    Try to discover the internal address by sending out a multicast
    message and inspect the response.
    
    @return: a L{Deferred} called with the internal address.
    """
    return MulticastDiscoverProtocol().discover()


@defer.inlineCallbacks
def discoverInternalHost():
    """
    Discover internal (aka local) IP address.
    
    @return: a deferred that will be called with the internal address.
    @rtype: L{Deferred}
    """
    for discover in (connectedSocketDiscover, localNetworkMulticastDiscover):
        try:
            value = yield discover()
            defer.returnValue(value)
        except Exception:
            print "CAUGHT"
            continue
    raise DiscoverError()
