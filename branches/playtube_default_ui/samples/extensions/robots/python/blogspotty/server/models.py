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

from google.appengine.ext import db


_LOGIN_HAS_QUERY = "SELECT * FROM Login WHERE waveid = :1 AND userid = :2"
# A record of a user logging in.
class Login(db.Model):

  waveid = db.StringProperty(required=True)
  userid = db.StringProperty(required=True)
  token = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)

  @staticmethod
  def exists(waveid, userid):
    query = db.GqlQuery(_LOGIN_HAS_QUERY, waveid, userid)
    for result in query.fetch(1):
      return True
    return False

  @staticmethod
  def get_token(waveid, userid):
    query = db.GqlQuery(_LOGIN_HAS_QUERY, waveid, userid)
    for result in query.fetch(1):
      return result.token
    return None

  @staticmethod
  def clear_permissions(userid):
    query = db.GqlQuery("SELECT __key__ FROM Login WHERE userid = :1", userid)
    db.delete(query)


# A connection between a wave and blogger.
class Connection(db.Model):

  waveid = db.StringProperty(required=True)
  owner = db.StringProperty(required=True)
  blog = db.StringProperty(required=False)
  feed_link = db.StringProperty(required=False)
  html_link = db.StringProperty(required=False)
  created = db.DateTimeProperty(auto_now_add=True)

  @staticmethod
  def get(waveid):
    query = db.GqlQuery("SELECT * FROM Connection WHERE waveid = :1 ORDER BY created ASC", waveid)
    for result in query.fetch(1):
      return result
  
  @staticmethod
  def get_by_url(url):
    query = db.GqlQuery("SELECT * FROM Connection WHERE html_link = :1 ORDER BY created ASC", url)
    for result in query.fetch(1):
      return result
