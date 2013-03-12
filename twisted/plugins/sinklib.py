####################################################################
# FILENAME: smtpsinkd/sinklib.py
# PROJECT: Charon
# DESCRIPTION: SMTP Sink Server Library
#
#
####################################################################
# (C)2012 DigiTar, All Rights Reserved
# CONFIDENTIAL
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

