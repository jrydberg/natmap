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


from twisted.internet import defer
from twisted.python import failure


class InstanceFactory:
    """
    Factory for creating instance of something.
    """

    def buildInstance(self):
        return None
        

class DeferredSingleton:
    """
    Container for a single instance of a class.

    The creation of the instance is made by a provided factory, and is
    deferred to when the instance is fetched for the first time.
    """

    def __init__(self, factory):
        self.factory = factory
        self.instance = None
        self.waiters = list()

    def _ebFactory(self, reason):
        """
        Callback for handling errors from the factory.
        """
        waiters = list(self.waiters)
        del self.waiters[:]

        for waiter in waiters:
            waiter.errback(reason)

    def _cbFactory(self, instance):
        """
        Callback for handling result from factory.
        """
        self.instance = instance
            
        waiters = list(self.waiters)
        del self.waiters[:]

        for waiter in waiters:
            waiter.callback(instance)

        return instance

    def get(self):
        """
        Get instance.

        @return: a deferred that will be called with the instance
        @rtype: L{Deferred}
        """
        if self.instance is None:
            deferred = defer.Deferred()

            if not len(self.waiters):
                d = defer.maybeDeferred(self.factory.buildInstance)
                d.addCallback(self._cbFactory).addErrback(self._ebFactory)

            self.waiters.append(deferred)
            return deferred

        return defer.succeed(self.instance)
