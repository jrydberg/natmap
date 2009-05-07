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
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol


class ConnectedSocketDiscover:
    """
    Internal IP discover mechanism that uses the a connected UDP socket.
    """
    implements(IPlugin, IDiscover)
    
    def discover(self):
        """
        Try to discover internal IP address.

        @rtype: L{Deferred}
        """
        def cb(address):
            protocol = DatagramProtocol()
            listeningPort = reactor.listenUDP(0, protocol)
            protocol.transport.connect(address, 7)
            internal = protocol.transport.getHost().host
            listeningPort.stopListening()
            return internal
        return reactor.resolve('A.ROOT-SERVERS.NET').addCallback(cb)

discover = ConnectedSocketDiscover()
