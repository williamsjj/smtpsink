####################################################################
# FILENAME: smtpsink/smtpsinkd.py
# PROJECT: Charon
# DESCRIPTION: SMTP Sink Server Tests
#
#
####################################################################
# (C)2012 DigiTar, All Rights Reserved
# CONFIDENTIAL
####################################################################

from twisted.application import service
from twisted.application import internet

from twisted.python import usage

import sinklib

service_maker = sinklib.SinkServiceMaker()