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

from natmap.inatmap import IDiscover, IMappingDeviceProvider
from natmap import discover as discoverPlugins
from natmap import devices as devicePlugins

from twisted.plugin import getPlugins, IPlugin
from twisted.internet import defer, reactor, error


discoverMechanisms = getPlugins(IDiscover, discoverPlugins)
deviceProviderMechanisms = getPlugins(IMappingDeviceProvider,
                                      devicePlugins)

class DiscoverError(Exception):
    """
    Internal address could not be discovered.
    """

    
@defer.inlineCallbacks
def discoverInternalAddress():
    """
    Discover internal (aka local) address.
    
    @return: a deferred that will be called with the internal address.
    @rtype: L{Deferred}
    """
    for discover in discoverMechanisms:
        try:
            value = yield discover.discover()
            defer.returnValue(value)
        except Exception:
            continue
    raise DiscoverError()


class MappingGroup:
    """
    Mapping group.
    """

    def __init__(self):
        self.mappings = list()

    def map(self, port, protocol):
        """
        """
        self.mappings.append((port, protocol))

    def unmap(self, port, protocol):
        self.mappings.remove((port, protocl))
            

class MappingDeviceDiscoverer:
    """
    Functionality for discovering mapping devices.
    """
    
    def __init__(self):
        self.device = None

    @defer.inlineCallbacks
    def discover(self):
        """
        Try to discover mapping device.
        """
        for provider in deviceProviderMechanisms:
            try:
                self.device = yield provider.search(10)
                defer.returnValue(self.device)
            except error.TimeoutError:
                continue
        raise DiscoverError()
            
    def get(self):
        """
        Return current mapping device or discover if not known at this
        time.

        @rtype: L{Deferred}
        """
        if self.device is not None:
            return deferred.succeed(self.device)
        return self.discover()

    
mappingDeviceDiscoverer = MappingDeviceDiscoverer()
discoverMappingDevice = mappingDeviceDiscoverer.get
