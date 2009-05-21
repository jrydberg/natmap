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

from twisted.trial import unittest
from twisted.internet import defer, address
from natmap import upnp, soap


class TestProxy:
    """
    Object that acts as a C{soap.Proxy}.
    """

    def __init__(self):
        self.mappings = list()
        self.external = '1.1.1.1'

    def GetExternalIPAddress(self):
        return defer.succeed(
            {'NewExternalIPAddress': self.external}
            )

    def callRemote(self, methodName, **kw):
        """
        Direct all calls to a local method.
        """
        return getattr(self, methodName)(**kw)

    def GetGenericPortMappingEntry(self, NewPortMappingIndex):
        if NewPortMappingIndex >= len(self.mappings):
            return defer.fail(soap.SOAPFault(None, None))
        return defer.succeed(self.mappings[NewPortMappingIndex])

    def AddPortMapping(self, **mapping):
        self.mappings.append(mapping)
        return defer.succeed(None)

            
class MapperTestCase(unittest.TestCase):

    def setUp(self):
        self.proxy = TestProxy()
        self.mapper = upnp.UPnPMapper(self.proxy)

    def cbExternalHost(self, externalHost):
        self.assertEquals(externalHost, '1.1.1.1')

    def ebExternalHost(self, reason):
        self.assertTrue(False, "error raised")

    def test_discoverExternalHost(self):
        """
        Verify that the external IP address can be retrieved.
        """
        d = self.mapper.discoverExternalHost()
        return d.addCallbacks(self.cbExternalHost, self.ebExternalHost)

    def cbMapAddress(self, externalAddress):
        self.assertEquals(externalAddress.type, 'TCP')
        self.assertEquals(externalAddress.host, '1.1.1.1')
        self.assertTrue(externalAddress.port > 1024
                        and externalAddress.port < 65535)

    def ebMapAddress(self, reason):
        self.assertTrue(False, "error raised")
    
    def test_mapAddress(self):
        """
        Verify that a L{IPv4Address} can be mapped.
        """
        d = self.mapper.map(address.IPv4Address('TCP', '192.168.1.1', 1322))
        return d.addCallbacks(self.cbMapAddress, self.ebMapAddress)
    
