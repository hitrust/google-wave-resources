import wsgiref.handlers
import logging
import string
import os

from google.appengine.ext import webapp
from django.utils import simplejson
from google.appengine.ext.webapp import template


from waveapi import search
import oauth_handler
import wave_renderer

class InboxHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return

    query = self.request.get('query', 'in:inbox')
    num_results = self.request.get('numResults', '20')
    results = self._service.search(query=query, num_results=num_results)
    template_values = {
      'digests': results.digests
    }
    path = os.path.join(os.path.dirname(__file__), 'templates/inbox.html')
    self.response.out.write(template.render(path, template_values))


class FetchWaveHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return
    SAMPLE_WAVE_ID = 'googlewave.com!w+SgYrEnoLE'
    wave_id = self.request.get('wave_id', SAMPLE_WAVE_ID)
    wave_id = wave_id.replace('%2B', '+')
    wavelet = self._service.fetch_wavelet(wave_id)
    tree = wave_renderer.render_wavelet(wavelet)
    template_values = {
      'json': simplejson.dumps(tree) 
    }
    path = os.path.join(os.path.dirname(__file__), 'templates/wave.html')
    self.response.out.write(template.render(path, template_values))


class MainHandler(webapp.RequestHandler):

  def get(self):
    self.redirect('/oauth/login')

def main():
  application = webapp.WSGIApplication([
                                        ('/', MainHandler),
                                        ('/app/inbox', InboxHandler),
                                        ('/app/fetchwave', FetchWaveHandler),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
