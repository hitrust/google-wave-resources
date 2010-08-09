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

import gdata.auth
import gdata.service
import models
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import urllib
from utils import to_json, Blogger

_ROOT_ADDRESS = "https://blogspotty.appspot.com"
_UPGRADE_URL = _ROOT_ADDRESS + "/server/upgradeToken"

_CLOSE_PAGE = """
<html>
  <head>
    <scipt>function close() { setTimeout(function () { window.close(); }, 0); }</script>
  </head>
  <body onload="close()"></body>
</html>
"""

class ServerHandler(webapp.RequestHandler):

  def __init__(self, **kwargs):
    super(ServerHandler, self).__init__(**kwargs)
    self.actions_ = {}
    self.actions_['authUrl'] = (self.get_auth_url, 'text/javascript')
    self.actions_['upgradeToken'] = (self.upgrade_token, 'text/html')
    self.actions_['authCheck'] = (self.check_user_auth, 'text/javascript')
    self.actions_['listBlogs'] = (self.list_blogs, 'text/javascript')
    self.actions_['waveLink'] = (self.wave_link_redirect, None)

  def check_user_auth(self):
    waveid = self.request.get('waveid')
    userid = self.request.get('userid')
    if (not waveid) or (not userid):
      return
    return to_json({
      'isSignedIn': models.Login.exists(waveid, userid)
    })

  def get_auth_url(self):
    waveid = self.request.get('waveid')
    userid = self.request.get('userid')
    if (not waveid) or (not userid):
      return
    return to_json({
      'url': Blogger.get_auth_url(waveid, userid, _UPGRADE_URL)
    })

  def upgrade_token(self):
    waveid = self.request.get('waveid')
    userid = self.request.get('userid')
    if (not waveid) or (not userid):
      return
    blogger_service = gdata.service.GDataService()
    auth_token = gdata.auth.extract_auth_sub_token_from_url(self.request.uri)
    if auth_token:
      session_token = blogger_service.upgrade_to_session_token(auth_token)
      token_string = session_token.get_token_string()
      login = models.Login(waveid=waveid, userid=userid, token=token_string)
      login.put()
    return _CLOSE_PAGE
  
  def list_blogs(self):
    blogs = Blogger.list_blogs()
    return to_json(blogs)
  
  def wave_link_redirect(self):
    waveid = self.request.get('waveid')
    connection = models.Connection.get(waveid)
    if connection and connection.html_link:
      self.redirect(connection.html_link)
    else:
      id = urllib.quote(waveid)
      self.redirect("https://wave.google.com/wave/?pli=1#restored:wave:%s" % id)

  def get(self, action):
    (handler, mime_type) = self.actions_.get(action, (None, None))
    if handler:
      content = handler()
      if content:
        if mime_type:
          self.response.headers['Cache-Control'] = 'private, no-cache'
          self.response.headers['Expires'] = 'Wed, 17 Sep 1975 21:32:10 GMT'
          self.response.headers['Content-Type'] = mime_type
        self.response.out.write(content)

def main():
  app = webapp.WSGIApplication([
    ('/server/(.*)', ServerHandler)
  ], debug=True)
  run_wsgi_app(app)

if __name__ == '__main__':
  main()
