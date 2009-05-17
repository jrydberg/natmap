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

from twisted.web import client


ENV = Namespace("http://schemas.xmlsoap.org/soap/envelope/", "s")


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
        print "url", self.url
        print "postdata", repr(postdata)
        return client.getPage(
            self.url, postdata=postdata, method="POST",
            headers=headers).addCallback(self.parseResponse)
