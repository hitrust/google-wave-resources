#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
import logging
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson

import models
import util

class ConfigHandler(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.dirname(__file__), 'templates/config.xml')
    self.response.headers['Content-Type'] = 'text/xml' 
    self.response.out.write(template.render(path, {}))

class GetPresetsHandler(webapp.RequestHandler):
  def get(self):
    presets_list = []
    preset_names = {}
    if self.request.get('viewer'):
      logging.info('querying viewer' + self.request.get('viewer'))
      q = models.TriagePreset.all()
      q.filter('creator =', self.request.get('viewer'))
      presets = q.fetch(20)
      for preset in presets:
        preset_names[preset.name] = 'seen'
        presets_list.append(preset.GetDict())

    q = models.TriagePreset.all()
    q.filter('public =', True)
    presets = q.fetch(100)
    for preset in presets:
      if preset.name not in preset_names:
        presets_list.append(preset.GetDict())

    json = simplejson.dumps(presets_list)
    self.response.out.write(json)


class GetPresetHandler(webapp.RequestHandler):
  def get(self):
    preset_key = self.request.get('preset_key')
    preset = models.TriagePreset.get(preset_key)
    json = simplejson.dumps(preset.GetDict())
    self.response.out.write(json)


class EditPresetHandler(webapp.RequestHandler):
  def get(self):
    # fill form with preset info
    preset_key = self.request.get('preset_key')
    preset = models.TriagePreset.get(preset_key)
    if preset is None:
      # error somehow
      pass
    sources = preset.GetSourcesList()
    template_values = {'preset': preset, 'sources': sources}
    path = os.path.join(os.path.dirname(__file__), 'templates/form.html')
    self.response.out.write(template.render(path, template_values))

class SavePresetHandler(webapp.RequestHandler):
  def post(self):
    name = self.request.get('name')
    sources = []
    source_num = 0
    source = self.request.get('source' + str(source_num))
    while source != '':
      source_project = self.request.get('source_project' + str(source_num))
      source_label = self.request.get('source_label' + str(source_num))
      source_status = self.request.get('source_status' + str(source_num))
      logging.info('project:' + source_project)
      logging.info('label:' + source_label)
      logging.info('status:' + source_label)
      sources.append({'type': 'code', 'project': source_project, 
                      'label': source_label, 'status': source_status})
      source_num += 1
      source = self.request.get('source' + str(source_num))

    key = self.request.get('key')
    if key != '':
      preset = models.TriagePreset.get(key)
    else:
      preset = models.TriagePreset()
      preset.creator = self.request.get('viewer')
      public = self.request.get('public')
      if public:
        preset.public = True

    preset.name = name
    preset.SetSourcesFromList(sources)
    preset.put()
    self.response.out.write('{}')


application = webapp.WSGIApplication(
                                     [
                                     ('/web/gadget', ConfigHandler),
                                     ('/web/edit', EditPresetHandler),
                                     ('/web/presets', GetPresetsHandler),
                                     ('/web/preset', GetPresetHandler),
                                     ('/web/save', SavePresetHandler)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
