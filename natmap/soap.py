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

from natmap.xmlbuilder import Namespace, LocalNamespace

from xml.etree.ElementTree import tostring, fromstring

from twisted.internet import reactor
from twisted.python import failure
from twisted.web import client


ENV = Namespace("http://schemas.xmlsoap.org/soap/envelope/", "s")


def getPage(url, contextFactory=None, *args, **kwargs):
    """Download a web page as a string.

    Download a page. Return a deferred, which will callback with a
    page (as a string) or errback with a description of the error.
    
    See HTTPClientFactory to see what extra args can be passed.
    """
    scheme, host, port, path = client._parse(url)
    factory = client.HTTPClientFactory(url, *args, **kwargs)
    factory.noisy = False
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory is None:
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory)
    else:
        reactor.connectTCP(host, port, factory)
    return factory.deferred


class SOAPFault(Exception):
    """
    Representation of a fault raised by the remote host.

    """

    def __init__(self, faultString, faultDetail):
        self.faultString = faultString
        self.faultDetail = faultDetail


class Proxy:

    def __init__(self, url, namespace):
        self.url = url
        self.namespace = namespace

    def buildEnvelope(self, element):
        """
        Build a SOAP envelope around C{element}.
        """
        element = ENV['Envelope'](ENV['Body'](element))
        element.set(ENV['encodingStyle'],
                    "http://schemas.xmlsoap.org/soap/encoding/")
        return element
        
    def parseResponse(self, data):
        document = fromstring(data)
        try:
            responseElement = document[0][0]
        except IndexError:
            raise RuntimeError("BAD")
        result = {}
        for childElement in responseElement:
            result[childElement.tag] = childElement.text
        return result

    def parseFault(self, reason):
        """
        Parse fault from remote device.
        """
        try:
            document = fromstring(reason.value.response)
        except Exception, e:
            # Some devices give bad faults.
            # Dlink DIR-665 gives a faulty prefix.
            return failure.Failure(SOAPFault('', None))
        
        faultElement = document.find('.//' + ENV['Fault'])
        return failure.Failure(
            SOAPFault(faultElement.findtext(ENV['faultstring']),
                      faultElement.find(ENV['detail']))
            )
    
    def callRemote(self, method, **kw):
        """
        Call remote function.
        """
        methodElement = self.namespace[method]()
        for name, value in kw.iteritems():
            methodElement.append(
                LocalNamespace[name](str(value))
                )

        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': '%s#%s' % (self.namespace.uri,
                                     method)
            }
        
        envelope = self.buildEnvelope(methodElement)
        postdata = '<?xml version="1.0"?>' + tostring(envelope)
        d = getPage(self.url, postdata=postdata, method="POST", headers=headers)
        return d.addCallbacks(self.parseResponse, self.parseFault)
