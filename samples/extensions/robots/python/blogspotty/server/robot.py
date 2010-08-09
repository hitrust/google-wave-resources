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

from datetime import datetime
import html
import logging
import models
import utils
import time
from google.appengine.api import users
from waveapi import events
from waveapi import element
from waveapi import appengine_robot_runner
from waveapi import waveservice


_GADGET_URL = utils.ROOT_ADDRESS + "/gadget.xml"
_UPGRADE_URL = utils.ROOT_ADDRESS + "/server/upgradeToken"


class Gadget(object):
  """Wrapper around a gadget ref that adds accessors.  The accessors
  cons up a number of changes and only update the gadget when submit
  is called."""

  STATUS_KEY = 'status'
  LOGIN = 'login'
  LOGGED_IN = 'logged_in'
  CONNECTED = 'connected'
  
  PUBLISH_MODE_KEY = 'publish_mode';
  PUBLISH_NONE = 'none';
  PUBLISH_AUTO = 'auto';
  PUBLISH_MANUAL = 'manual';
  PUBLISH_DRAFT = 'draft';
  
  REQUEST_KEY = 'request'
  REQUEST_CONNECT = 'connect'
  REQUEST_PUBLISH = 'publish'
  REQUEST_SAVE_DRAFT = 'save_draft'
  REQUEST_NONE = 'none'
  
  OWNER_KEY = 'owner'
  URL_KEY = 'post_url'
  TITLE_KEY = 'post_title'
  POST_TIME_KEY = 'post_time'

  def __init__(self, ref):
    self.ref_ = ref
    self.props_ = {}

  def set_status(self, state):
    return self.set(Gadget.STATUS_KEY, state)

  def set_owner(self, value):
    return self.set(Gadget.OWNER_KEY, value)
  
  def set_url(self, value):
    return self.set(Gadget.URL_KEY, value)
  
  def set_title(self, value):
    return self.set(Gadget.TITLE_KEY, value)
  
  def set_post_time(self, time):
    return self.set(Gadget.POST_TIME_KEY, time)
  
  def get_owner(self):
    return self.get(Gadget.OWNER_KEY)

  def get_status(self):
    return self.get(Gadget.STATUS_KEY, 'none')
  
  def get_request(self):
    return self.get(Gadget.REQUEST_KEY, Gadget.REQUEST_NONE)
  
  def clear_request(self):
    return self.set(Gadget.REQUEST_KEY, Gadget.REQUEST_NONE)

  def get_publish_mode(self):
    return self.get(Gadget.PUBLISH_MODE_KEY, Gadget.PUBLISH_NONE)

  def set(self, key, value):
    self.props_[key] = value
    return self

  def get(self, key, default = None):
    if key in self.props_:
      return self.props_.get(key, default)
    return self.ref_.get(key, default)

  def get_state(self):
    result = dict(self.props_)
    for key in self.ref_.keys():
      if not key in result:
        result[key] = self.ref_.get(key)
    return result

  def submit(self):
    self.ref_.update_element(self.props_)


_OUTPUT_TEMPLATE = '''\
<script type="text/javascript" src="https://blogspotty.appspot.com/static/post.js"></script>
%(body)s
'''


class Robot(object):

  def __init__(self):
    self.robot_ = None
    self.command_handlers_ = {}
    self.command_handlers_['dump gadget state'] = self.do_dump_gadget_state_command
    self.command_handlers_['restore gadget'] = self.do_restore_gadget_command
    self.command_handlers_['clear my permissions'] = self.do_clear_my_permissions_command
    self.command_handlers_['list commands'] = self.do_list_commands_command
    self.command_handlers_['publish'] = self.do_publish_command

  def find_gadget(self, wavelet):
    for blip in wavelet.blips.values():
      ref = blip.first(element.Gadget, url=_GADGET_URL)
      if ref:
        return Gadget(ref)
    return None

  def is_root_blip(self, blip, wavelet):
    return blip == wavelet.root_blip

  def on_blip_submitted(self, event, wavelet):
    if self.is_root_blip(event.blip, wavelet):
      self.on_root_blip_submitted(event, wavelet)
    else:
      self.on_other_blip_submitted(event, wavelet)

  def on_root_blip_submitted(self, event, wavelet):
    gadget = self.find_gadget(wavelet)
    if gadget is None:
      return
    if gadget.get_status() != Gadget.CONNECTED:
      return
    if gadget.get_publish_mode() != Gadget.PUBLISH_AUTO:
      return
    self.on_publish(gadget, wavelet)
    gadget.submit()

  # Invoked when any other blip than the root blip is submitted.  This
  # is used to invoke commands if you reply with the magic words
  # "blogspotty, please <command>".
  def on_other_blip_submitted(self, event, wavelet):
    text = event.blip.text.lower().strip()
    command_marker = "blogspotty, please"
    if text.startswith(command_marker):
      kwargs = {}
      gadget = self.find_gadget(wavelet)
      if gadget:
        kwargs['gadget'] = gadget
      command = text[len(command_marker):].strip()
      handler = self.command_handlers_.get(command)
      if handler and handler(event, wavelet, **kwargs):
        wavelet.delete(event.blip)

  def do_dump_gadget_state_command(self, event, wavelet, gadget=None):
    if not gadget:
      return False
    wavelet.reply(utils.to_json(gadget.get_state()))
    return True

  def do_restore_gadget_command(self, event, wavelet, gadget=None):
    if gadget:
      return True
    self.on_wavelet_self_added(event, wavelet)
    return True

  def do_clear_my_permissions_command(self, event, wavelet, gadget=None):
    count = models.Session.clear_permissions(event.modified_by)
    wavelet.reply("Cleared all permissions for %s." % event.modified_by)
    return True

  def do_list_commands_command(self, event, wavelet, gadget=None):
    keys = sorted(self.command_handlers_.keys())
    wavelet.reply().append_markup("<ul>%s</ul>" % "".join(["<li>%s</li>" % k for k in keys]))
    return True
  
  def do_publish_command(self, event, wavelet, gadget=None):
    if not gadget:
      return False
    self.on_publish(gadget, wavelet)
    return True

  def on_publish(self, gadget, wavelet, is_draft=False):
    connection = models.Connection.get(wavelet.wave_id)
    if not connection:
      return False
    blogger = utils.Blogger.open(wavelet.wave_id, connection.owner)
    if not blogger:
      return False
    body = html.to_html(wavelet.root_blip)
    contents = _OUTPUT_TEMPLATE % {
      'body': body
    }
    post = blogger.publish(connection.blog, connection.feed_link, wavelet.title,
        contents, is_draft)
    link = post.get_html_link()
    if link:
      url = link.href
      title = link.title
      if not connection.feed_link:
        connection.feed_link = post.get_self_link().href
        connection.html_link = url
        connection.put()
    else:
      url = None
      title = None
    gadget.set_url(url)
    gadget.set_title(title)
    tz = time.timezone
    if tz >= 0:
      sign = '+'
    else:
      sign = ''
    post_time = datetime.now().strftime('%a, %d %b %Y %H:%M:%S ') + sign + str(tz)
    gadget.set_post_time(post_time)

  def on_wavelet_blip_created(self, event, wavelet):
    pass

  def on_wavelet_blip_removed(self, event, wavelet):
    pass

  # We've just been added to a wave.  Add a new blip containing the
  # control gadget in the LOGIN state.
  def on_wavelet_self_added(self, event, wavelet):
    new_blip = wavelet.reply("")
    new_gadget = element.Gadget(_GADGET_URL)
    new_blip.append(new_gadget)
    gadget = Gadget(new_blip.first(element.Gadget, url=_GADGET_URL))
    waveid = wavelet.wave_id
    gadget.set_status(Gadget.LOGIN)
    gadget.submit()

  def on_logged_in(self, userid, gadget, wavelet):
    waveid = wavelet.wave_id
    if not models.Login.exists(waveid, userid):
      # Wait, this user has no login.  Bail out.
      gadget.set_status(Gadget.LOGIN)
      return
    blogger = utils.Blogger.open(wavelet.wave_id, userid)
    if not blogger:
      # There was some error.  Bail out.
      gadget.set_status(Gadget.LOGIN)
      return
    blogs = blogger.get_blogs()
    if len(blogs) == 0:
      # User has no blogs.  Bail out for now.
      gadget.set_status(Gadget.LOGIN)
      return
    blog = blogs[0]['id']
    connection = models.Connection.get(waveid)
    if connection:
      connection.owner = userid
      connection.blog = blog
      connection.post = None
    else:
      connection = models.Connection(waveid=waveid, owner=userid, blog=blog)
    connection.put()
    gadget.set_owner(userid)
    gadget.set_status(Gadget.CONNECTED)
    gadget.set('blogs', utils.to_json(blogs))
    gadget.set('blog', blog)

  def on_gadget_state_changed(self, event, wavelet):
    blip = event.blip
    gadget = Gadget(blip.at(event.index))
    request = gadget.get_request()
    old_request = event.old_state.get(Gadget.REQUEST_KEY)
    if (request == Gadget.REQUEST_NONE) or (request == old_request):
      return
    gadget.clear_request()
    if request == Gadget.REQUEST_CONNECT:
      owner = event.modified_by
      self.on_logged_in(owner, gadget, wavelet)
    elif request == Gadget.REQUEST_PUBLISH:
      self.on_publish(gadget, wavelet, is_draft=False)
    elif request == Gadget.REQUEST_SAVE_DRAFT:
      self.on_publish(gadget, wavelet, is_draft=True)
    gadget.submit()

  def main(self):
    service = utils.create_robot()
    self.robot_ = service
    service.register_handler(events.BlipSubmitted, self.on_blip_submitted, context=[events.Context.ALL])
    service.register_handler(events.WaveletBlipCreated, self.on_wavelet_blip_created)
    service.register_handler(events.WaveletBlipRemoved, self.on_wavelet_blip_removed)
    service.register_handler(events.WaveletSelfAdded, self.on_wavelet_self_added)
    service.register_handler(events.GadgetStateChanged, self.on_gadget_state_changed)
    appengine_robot_runner.run(service)

if __name__ == '__main__':
  Robot().main()
