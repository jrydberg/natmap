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

# This is a small example of how to create a publicly mapped service.

from twisted.application import internet, service
from twisted.internet import protocol
from natmap import mapListeningPort, unmapListeningPort


class MappedTCPServer(internet.TCPServer):

    def cbMapped(self, externalAddress):
        self._external = externalAddress
        if hasattr(self, "serviceMapped"):
            self.serviceMapped(self._external)

    def startService(self):
        internet.TCPServer.startService(self)
        mapListeningPort(self._port).addCallback(self.cbMapped)

    def stopService(self):
        if self._port is not None:
            def cb(*whatever):
                return internet.TCPServer.stopService(self)
            return unmapListeningPort(self._port).addCallback(cb)


class EchoProtocol(protocol.Protocol):

    def dataReceived(self, data):
        self.transport.write(data)


class EchoFactory(protocol.Factory):

    protocol = EchoProtocol


class EchoServer(MappedTCPServer):

    def __init__(self):
        internet.TCPServer.__init__(self, 0, EchoFactory())

    def serviceMapped(self, address):
        print "echo service is available at", address.host, address.port


application = service.Application("mapped-service")
mappedService = EchoServer()
mappedService.setServiceParent(application)
