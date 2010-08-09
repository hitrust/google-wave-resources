# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__authors__ = ['christian.plesner.hansen@gmail.com (Christian Plesner Hansen)']

# Sigh...
import sys
import os.path
sys.path.append(os.path.dirname(__file__))

# Service for receiving comment notifications from blogs and adding them as
# replies on the respective waves.

import email
import logging
import models
import re
import utils
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app
from waveapi import robot

_BLOGGER_COMMENT_MATCHER = re.compile(r"^<a href=\"http://www.blogger.com/profile/([0-9]+)\">[^<]*</a>[^<]*<a href=\"(http://[^\"]*\.html)\">")

class CommentRobot(object):
  
  def __init__(self):
    self.robot_ = utils.create_robot()

  def get_payload(self, message):
    for (mime_type, data) in message.bodies('text/html'):
      return data.decode()

  def receive(self, message):
    payload = self.get_payload(message)
    match = _BLOGGER_COMMENT_MATCHER.search(payload)
    if not match:
      logging.info("No match in %s" % payload)
      return
    user_id = "blogger." + match.group(1)
    url = match.group(2)
    connection = models.Connection.get('googlewave.com!w+f3Jl4FDGA')
    waveid = connection.waveid
    wavelet = self.robot_.fetch_wavelet(waveid)
    wavelet.robot_address = utils.ROBOT_USER_ADDRESS
    proxy = wavelet.proxy_for(user_id)
    proxy.reply(payload)
    self.robot_.submit(wavelet)

  def get_class(self):
    outer = self
    class Handler(InboundMailHandler):
      def receive(self, message):
        outer.receive(message)
    return Handler


def main():
  robot = CommentRobot()
  app = webapp.WSGIApplication([robot.get_class().mapping()], debug=True)
  run_wsgi_app(app)


if __name__ == '__main__':
  main()
