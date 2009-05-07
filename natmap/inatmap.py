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


class IDiscover(Interface):
    """
    A device that can discover IP addresses.
    """

    def discover():
        """
        Try to internal address.

        @rtype: L{Deferred}
        """


class IMappingGroup(Interface):
    """
    Group of mappings.

    Mappings that have the same characteristics can be grouped
    together to ease tear down.
    """

    def map(port, protocol):
        """
        Map internal port C{port}.

        @type port: C{int}
        @type protocol: C{str} that is C{'udp'} or C{'tcp'}
        @rtype: C{Deferred}
        """

    def unmap(port, protocol):
        """
        Unmap internal port C{port}.

        Fails with C{ValueError} if there is no such mapping.

        @type port: C{int}
        @type protocol: C{str} that is C{'udp'} or C{'tcp'}
        @rtype: C{Deferred}
        """


class IMappingDevice(Interface):
    """
    Mapping device is responsible for establishing mappings.
    """

    def createMappingGroup():
        """
        Create and return a new L{IMappingGroup}.
        """

    def mapGroup(group):
        """
        Map all mappings in the given group.

        @rtype: L{Deferred}
        """

    def unmapGroup(group):
        """
        Unmap all mappings in the given group.

        @rtype: L{Deferred}
        """


class IMappingDeviceProvider(Interface):
    """
    Provider of C{IMappingDevice}
    """

    def search(timeout):
        """
        Search for mapping device.  Stop if no device was found in
        C{timeout} seconds.
        
        @return: a deferred called with a L{IMappingDevice}
        @rtype: L{Deferred}
        """
