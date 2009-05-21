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

from natmap.util import DeferredSingleton, InstanceFactory
from natmap.upnp import discoverMapper as discoverUPnPMapper
from natmap.mapper import MapperReactor 
from natmap.internal import discoverInternalHost

from twisted.internet import defer


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


mapperReactor = MapperReactor(MapperInstanceFactory())
mapAddress = mapperReactor.mapAddress
mapListeningPort = mapperReactor.mapListeningPort
unmapListeningPort = mapperReactor.unmapListeningPort
discoverExternalHost = mapperReactor.discoverExternalHost

__all__ = ['mapAddress', 'mapListeningPort', 'unmapListeningPort',
           'discoverInternalHost', 'discoverExternalHost']
