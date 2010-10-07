#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc.
# Licensed under the Apache License, Version 2.0:
# http://www.apache.org/licenses/LICENSE-2.0

"""The module that handles requests for services.
"""

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache

from django.utils import simplejson

import models

class IsFollowing(webapp.RequestHandler):
  def get(self):
    #
    creator = self.request.get('creator')
    viewer = self.request.get('viewer')
    # check if viewer is following creator
    rippler = models.GetOrCreateRippler(viewer)
    if creator in rippler.following:
      answer = 'yes'
    else:
      answer = 'no'
    json = '{"status": "success", "answer": "%s"}' % answer
    self.response.out.write(json)

class Follow(webapp.RequestHandler):
  def get(self):
    creator = self.request.get('creator')
    viewer = self.request.get('viewer')
    # make viewer follow creator
    rippler = models.GetOrCreateRippler(viewer)
    if creator not in rippler.following:
      rippler.following.append(creator)
      rippler.put()
    json = '{"status": "success", "answer": "yes"}'
    self.response.out.write(json)

class UnFollow(webapp.RequestHandler):
  def get(self):
    creator = self.request.get('creator')
    viewer = self.request.get('viewer')
    # make viewer follow creator
    rippler = models.GetOrCreateRippler(viewer)
    if creator in rippler.following:
      rippler.following.remove(creator)
    rippler.put()
    json = '{"status": "success", "answer": "no"}'
    self.response.out.write(json)
