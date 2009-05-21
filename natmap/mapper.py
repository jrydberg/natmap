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

from natmap.inatmap import IMapper

from natmap.util import DeferredSingleton, InstanceFactory
from natmap.upnp import discoverMapper as discoverUPnPMapper
from natmap.internal import discoverInternalHost

from twisted.internet import defer, reactor, error
from twisted.internet.address import IPv4Address


class MapperInstanceFactory:
    """
    Instance factory for building something that provides IMapper.
    """

    @defer.inlineCallbacks
    def buildInstance(self):
        for discover in (discoverUPnPMapper,):
            try:
                mapper = yield discover()
                defer.returnValue(mapper)
            except Exception:
                continue
        raise RuntimeError("no mapper available")


class MapperReactor:

    def __init__(self, factory):
        self.singleton = DeferredSingleton(factory)
    def ensureInternalAddress(self, address):
        """
        Ensure that address is a valid internal address and if not
        turn it into one.
        
        @rtype: L{Deferred}
        """
        if address.host in ('0.0.0.0', '127.0.0.1', ''):
            def cb(internalHost, address=address):
                return IPv4Address(
                    address.type, internalHost, address.port
                    )
            return discoverInternalHost().addCallback(cb)

        return defer.succeed(address)

    def discoverExternalHost(self):
        """
        """
        def cb(mapper):
            return mapper.discoverExternalHost()
        return self.singleton.get().addCallback(cb)

    def mapAddress(self, address):
        """
        Map internal address C{address} to an external address.

        @type address: L{IPv4Address}
        @return: a deferred called with the external address.
        """
        def cb(mapper):
            return mapper.map(address)
        return self.singleton.get().addCallback(cb)

    def unmapAddress(self, address):
        """
        Unmap internal address C{address}.

        @type address: L{IPv4Address}
        """
        def cb(mapper):
            return mapper.unmap(address)
        return self.singleton.get().addCallback(cb)

    def mapListeningPort(self, listeningPort):
        """
        Map listening port.

        @type listeningPort: L{IListeningPort} provider.
        """
        def cb(address):
            return self.mapAddress(address)
        return self.ensureInternalAddress(
            listeningPort.getHost()).addCallback(cb)
    
    def unmapListeningPort(self, listeningPort):
        """
        Unmap listening port.

        @type listeningPort: L{IListeningPort} provider.
        """
        def cb(address):
            return self.unmapAddress(address)
        return self.ensureInternalAddress(
            listeningPort.getHost()).addCallback(cb)
