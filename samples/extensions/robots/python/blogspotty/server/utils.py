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

import atom.data
import credentials
import gdata.auth
import gdata.service
import gdata.blogger.client
import gdata.client
import logging
import models
import profiles
import urllib
from waveapi import robot

ROOT_ADDRESS = "https://blogspotty.appspot.com"
ROBOT_USER_ADDRESS = "blogspotty@appspot.com"



_ESCAPEES = {
  '"': '\\"',
  '\\': '\\\\',
  '\b': '\\b',
  '\f': '\\f',
  '\n': '\\n',
  '\r': '\\r',
  '\t': '\\t'
}

def json_escape(s):
  result = []
  for c in s:
    escapee = _ESCAPEES.get(c, None)
    if escapee:
      result.append(escapee)
    elif c < ' ':
      result.append("\\u%.4X" % ord(c))
    else:
      result.append(c)
  return "".join(result)

def to_json(obj):
  t = type(obj)
  if t is dict:
    props = [ ]
    for (key, value) in obj.items():
      props.append('"%s": %s' % (json_escape(key), to_json(value)))
    return '{%s}' % ', '.join(props)
  elif (t is int) or (t is long):
    return str(obj)
  elif (t is str) or (t is unicode):
    return '"%s"' % json_escape(obj)
  elif (t is list):
    return '[%s]' % ', '.join([to_json(o) for o in obj])
  elif t is bool:
    if obj: return '1'
    else: return '0'
  else:
    return to_json(obj.to_json())

# Convenience wrapper around the blogger gdata service.
class Blogger(object):

  def __init__(self, client, token):
    self.client_ = client
    self.token_ = token

  # Returns a list of blogs belonging to the default user.
  def get_blogs(self):
    blogs = self.client_.get_blogs(auth_token=self.token_)
    def blog_to_json(blog):
      return {'title': blog.title.text, 'id': blog.get_blog_id()}
    return [blog_to_json(entry) for entry in blogs.entry]
  
  def publish(self, blog, post, title, content, is_draft):
    if post:
      entry = self.client_.get_entry(uri=post, auth_token=self.token_)
      entry.title.text = title
      entry.content.text = content
      if is_draft:
        draft_value = 'yes'
      else:
        draft_value = 'no'
      entry.control = atom.data.Control(draft=atom.data.Draft(text=draft_value))
      return self.client_.update(entry, auth_token=self.token_)
    else:
      return self.client_.add_post(blog, title, content, draft=is_draft,
          auth_token=self.token_)

  # Returns the blogger service for the given wave and user ids.  If
  # the user is not logged in for the given wave None is returned.
  @staticmethod
  def open(waveid, userid):
    token_string = models.Login.get_token(waveid, userid)
    if not token_string:
      return None
    token = gdata.gauth.AuthSubToken(token_string)
    client = gdata.blogger.client.BloggerClient()
    return Blogger(client, token)

  @staticmethod
  def list_blogs():
    client = gdata.blogger.client.BloggerClient()
    logging.info(str(client))
    blogs = client.get_blogs()
    logging.info(str(client))
    result = [blog_to_json(entry) for entry in blogs.entry]
    logging.info(str(result))
    return result

  # Returns the URL the user has to visit to allow blogspotty to
  # connect to blogger on their behalf.  See
  # http://code.google.com/apis/blogger/docs/1.0/developers_guide_python.html#AuthSub.
  @staticmethod
  def get_auth_url(waveid, userid, upgrade_url):
    blogger_service = gdata.service.GDataService()
    qwaveid = urllib.quote(waveid)
    quserid = urllib.quote(userid)
    url = blogger_service.GenerateAuthSubURL(
      next = '%s?waveid=%s&userid=%s' % (upgrade_url, qwaveid, quserid),
      scope = 'https://www.blogger.com/feeds/',
      secure = False,
      session = True)
    return str(url)


_RPC_BASE = "http://www-opensocial.googleusercontent.com/api/rpc"
def create_robot():
  service = robot.Robot(
    name = profiles.ROBOT_NAME,
    image_url = profiles.ROBOT_IMAGE_URL,
    profile_url = profiles.ROBOT_PROFILE_URL)
  service.register_profile_handler(profiles.ProfileResolver().get_profile)
  service.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET, server_rpc_base=_RPC_BASE)
  return service
