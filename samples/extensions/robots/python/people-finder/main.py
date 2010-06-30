#!/usr/bin/env python

import logging
import os

from django.utils import simplejson
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from interests import INTERESTS
from model import GTUG, Profile

from conference import CONFERENCE_TITLE

M_PER_KM = 1000.0
M_PER_MILE = 1609.344 

def distance_to_meters(distance, units):
  multiplier = M_PER_KM  # m/km 
  if units == 'miles':
    multiplier = M_PER_MILE  # m/mile
  return float(distance) * multiplier


class ExtensionHandler(webapp.RequestHandler):

  def get(self):
    template_values = { 
        'appid': os.environ['APPLICATION_ID'],
        'title': CONFERENCE_TITLE
        }
    path = os.path.join(os.path.dirname(__file__), 'templates', 'extension.xml')
    self.response.headers.add_header('Content-type', 'text/xml')
    self.response.out.write(template.render(path, template_values))

class Struct:
    def __init__(self, **entries): self.__dict__.update(entries)

class GadgetHandler(webapp.RequestHandler):

  def get(self):
    interests = [] 
    for id, label in INTERESTS:
      interests.append(Struct(id=id, label=label))
    template_values = { 
        'appid': os.environ['APPLICATION_ID'],
        'interests': interests 
        }
    path = os.path.join(os.path.dirname(__file__), 'templates', 'gadget.xml')
    self.response.headers.add_header('Content-type', 'text/xml')
    self.response.out.write(template.render(path, template_values))


class GTUGUpdateTask(webapp.RequestHandler):

  def post(self): 
    key = self.request.get('key')
    chapters= simplejson.loads(key)
    if chapters:
      chapter = chapters.pop()
      logging.info(chapter)
      gtug = GTUG.get_or_insert(chapter['name'])
      gtug.location = db.GeoPt(chapter['latitude'], chapter['longitude'])
      gtug.update_location()
      gtug.gtugid = chapter['id']
      gtug.url = chapter['url']
      gtug.put()
      taskqueue.add(url='/update-task', params={'key': simplejson.dumps(chapters)})
    else:
      logging.info("Finished adding GTUG chapters via task queue")


class GTUGFetcher(webapp.RequestHandler):

  def get(self):
    from google.appengine.api import urlfetch

    url = "http://www.gtugs.org/chapters"
    result = urlfetch.fetch(url)
    if result.status_code == 200:
      logging.info("Started adding GTUG chapters via task queue")
      gtugs = simplejson.loads(result.content)
      chapters = gtugs['chapters']
      while chapters:
        taskqueue.add(url='/update-task', params={'key': simplejson.dumps(chapters[0:20])})
        del chapters[0:20]
    else:
      logging.error("Failed to fetch GTUG JSON: %d", result.status_code)


class Search(webapp.RequestHandler):

  def get(self):
    creator = self.request.get('creator', '')
    logging.info("Creator: %s", creator);
    logging.info(self.request.arguments())
    distance = self.request.get('distance', '')
    msg = ""
    found = []
    matches = Profile.all().filter('creator =', creator).fetch(1)
    if matches:
      user = matches[0]
    else:
      user = None
    results = []
    query = Profile.all()

    keys = dict(INTERESTS)
    for interest in self.request.arguments():
      if interest in keys:
        query = query.filter("interests =", interest)
        logging.info("interests = %s" % interest)
    if user and distance:
      if user.location is None:
        msg = "You need to enter your position on the map in your People Finder Profile wave before doing a location based search"
        results = query.fetch(20)
      else:
        max_distance = distance_to_meters(distance, self.request.get('units', ''))
        results = Profile.proximity_fetch(
          query,
          user.location,  # Or db.GeoPt
          max_results=20,
          max_distance=max_distance # meters
        ) 
    else:
      results = query.fetch(20)

    if user:
      found = [{'name': r.name, 'id': r.creator} for r in results if r.key().name() != user.key().name()]
    else:
      found = [{'name': r.name, 'id': r.creator} for r in results]
    gtugs = simplejson.dumps({'msg': msg, 'results': found})
    logging.info("response: %s" % gtugs)
    self.response.headers.add_header('Content-type', 'application/json')
    self.response.out.write(gtugs)

def main():
  application = webapp.WSGIApplication(
      [
        ('/extension.xml', ExtensionHandler),
        ('/gadget.xml', GadgetHandler),
        ('/refresh-gtugs', GTUGFetcher),
        ('/update-task', GTUGUpdateTask),
        ('/search', Search),
        ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
