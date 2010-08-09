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

from google.appengine.api.urlfetch import fetch
import logging
import re

ROBOT_NAME = "Blogspotty"
ROBOT_IMAGE_URL =  "https://blogspotty.appspot.com/static/icon.png"
ROBOT_PROFILE_URL = "http://blogspotty.appspot.com"

ROBOT_PROFILE = {
  'name': ROBOT_NAME,
  'imageUrl': ROBOT_IMAGE_URL,
  'profileUrl': ROBOT_PROFILE_URL
}

class ProfileResolver(object):

  def __init__(self):
    self.domains_ = {}
    self.domains_['blogger'] = self.get_blogger_profile

  BLOGGER_NAME_RE = re.compile(r"<title>Blogger: User Profile: ([^<]*)</title>")
  BLOGGER_IMAGE_RE = re.compile(r"<img class=\"photo\" src=\"([^\"]*)\"")
  def get_blogger_profile(self, id):
    profile_url = 'http://www.blogger.com/profile/%s' % id
    response = fetch(profile_url)
    name = None
    image_url = None
    if response.status_code == 200:
      name_match = ProfileResolver.BLOGGER_NAME_RE.search(response.content)
      if name_match:
        name = name_match.group(1).strip()
      image_match = ProfileResolver.BLOGGER_IMAGE_RE.search(response.content)
      if image_match:
        image_url = image_match.group(1)
    if not name:
      name = id
    if not image_url:
      image_url = ROBOT_IMAGE_URL
    full_name = "Blogger user %s" % name
    return {'name': full_name, 'imageUrl': image_url, 'profileUrl': profile_url}
  
  def get_profile(self, name):
    if not name:
      return ROBOT_PROFILE
    else:
      parts = name.split('.')
      if len(parts) != 2:
        return None
      domain = self.domains_.get(parts[0])
      if not domain:
        return None
      return domain(parts[1])
