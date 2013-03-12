####################################################################
# FILENAME: smtpsinkd/sinklib.py
# PROJECT: Charon
# DESCRIPTION: SMTP Sink Server Library
#
#
####################################################################
# (C)2013 DigiTar, All Rights Reserved
# 
# Redistribution and use in source and binary forms, with or without modification, 
#    are permitted provided that the following conditions are met:
#
#        * Redistributions of source code must retain the above copyright notice, 
#          this list of conditions and the following disclaimer.
#        * Redistributions in binary form must reproduce the above copyright notice, 
#          this list of conditions and the following disclaimer in the documentation 
#          and/or other materials provided with the distribution.
#        * Neither the name of DigiTar nor the names of its contributors may be
#          used to endorse or promote products derived from this software without 
#          specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
# SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH 
# DAMAGE.
####################################################################

import time, os, sys
from zope.interface import implements
from twisted.internet import protocol, defer
from twisted.mail import smtp
from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.application import internet, service

class FileMessage(object):
    implements(smtp.IMessage)

    def __init__(self, storage_dir, helo, mail_from, rcpt_to):
        self.f = open("%s/%s_%s_%s_%s.txt" % (storage_dir,
                                              str(time.time()),
                                              helo,
                                              mail_from,
                                              rcpt_to), "w")

    def lineReceived(self, line):
        self.f.write(line + "\n")

    def eomReceived(self):
        self.f.close()
        return defer.succeed(None)

    def connectionLost(self):
        self.f.close()

class SinkDelivery(object):
    implements(smtp.IMessageDelivery)
    counter = 0
    
    def __init__(self, delivery_factory):
        self.delivery_factory = delivery_factory

    def validateTo(self, user):
        self.counter += 1
        return lambda: FileMessage(self.delivery_factory.esmtp_factory.storage_dir,
                                   self.helo,
                                   self.mail_from,
                                   str(user))

    def validateFrom(self, helo, origin):
        self.helo = helo[0]
        self.src_ip = helo[1]
        self.mail_from = "%s@%s" % (origin.local, origin.domain)
        return origin
    
    def receivedHeader(self, helo, origin, recipients):
        return ""

class SinkDeliveryFactory(object):
    implements(smtp.IMessageDeliveryFactory)
    
    def __init__(self, esmtp_factory):
        self.esmtp_factory = esmtp_factory
    
    def getMessageDelivery(self):
        return SinkDelivery(self)

class SinkESMTPFactory(protocol.ServerFactory):
    protocol = smtp.ESMTP
    storage_dir = ""
    
    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
    
    def buildProtocol(self, addr):
        p = self.protocol()
        p.deliveryFactory = SinkDeliveryFactory(self)
        p.factory = self
        return p

class Options(usage.Options):

    optParameters = [
        ['port', 'p', 25, 'The port number to listen on.'],
        ['directory', 'd', None, 'The directory to store messages in.']
        ]

class SinkServiceMaker(object):
    
    implements(service.IServiceMaker, IPlugin)
    
    tapname = "smtpsink"
    description = "An SMTP message sink."
    options = Options
    
    def makeService(self, options):
        if not os.path.exists(options['directory']):
            log.msg("Directory '%s' does not exist. Exiting." % options['directory'])
            sys.exit(-1)
        
        top_service = service.MultiService()
        factory = SinkESMTPFactory(options['directory'])
        tcp_service = internet.TCPServer(int(options['port']), factory)
        tcp_service.setServiceParent(top_service)
        return top_service

