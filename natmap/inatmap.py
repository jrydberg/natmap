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

from zope.interface import Interface


class IMapper(Interface):
    """
    Functionality for mapping an internal address to a external
    address and open up the NAT.
    """

    def discoverExternalHost():
        """
        Discover the external IP address.


        @return: A L{Deferred} that will be called with the external
            IP address.
        """

    def map(address):
        """
        Map internal address.

        @param address: internal address.
        @type address: L{twisted.internet.address.IPv4Address}

        @return: A L{Deferred} that will be called with the external
            address of the mapped port.
        """

    def unmap(address):
        """
        Unmap internal address.

        @param address: internal address.
        @type address: L{twisted.internet.address.IPv4Address}

        @return: A L{Deferred} that will be called when the mapping
            has been revoked.
        """
