#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
import logging
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson

import util
import model

class AdminHandler(webapp.RequestHandler):
  def get(self):
    is_gadget = self.request.get('gadget')
    type = self.request.get('type')
    filename = 'admin.xml'
    content_type = 'text/xml'
    template_values = {'server': util.GetServer(),
                       'conference_type': type}
    path = os.path.join(os.path.dirname(__file__), 'templates/' + filename)
    self.response.headers['Content-Type'] = content_type
    self.response.out.write(template.render(path, template_values))

class InstallerHandler(webapp.RequestHandler):
  def get(self):
    id = self.request.get('id')
    conference = model.Conference.get_by_id(int(id))
    if conference is None:
      self.response.out.write('Error: Couldnt find conference')
      return
    savedsearch = 'group:conference-waves@googlegroups.com tag:%s' % conference.hashtag
    template_values = {'name': conference.name,
                       'icon': conference.icon,
                       'id': conference.key().id(),
                       'include_savedsearch': conference.include_savedsearch,
                       'savedsearch': savedsearch,
                       'include_newwave': conference.include_newwave}
    path = os.path.join(os.path.dirname(__file__), 'templates/installer.xml')
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(template.render(path, template_values))


class InfoHandler(webapp.RequestHandler):
  def get(self):
    format = self.request.get('format', 'html')
    sessions_query = model.SessionInfo.all().order('-id')
    sessions = sessions_query.fetch(500)
    template_values = {'sessions': sessions}
    if format == 'html':
      path = os.path.join(os.path.dirname(__file__), 'templates/info.html')
      self.response.headers['Content-Type'] = 'text/html'
    else:
      path = os.path.join(os.path.dirname(__file__), 'templates/info.csv')
      self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [
                                     ('/web/admin', AdminHandler),
                                     ('/web/installer', InstallerHandler),
                                     ('/web/info', InfoHandler)
                                     ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
