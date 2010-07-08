import wsgiref.handlers
import logging
import string

from google.appengine.ext import webapp
from django.utils import simplejson

from waveapi import search
import oauth_handler
import wave_renderer
import results_renderer

def page_html(html):
  base_page = """
  <html><head>
  <link rel="stylesheet" type="text/css" href="http://wave-api.appspot.com/public/wave.ui.css">
  </head>
  <body>
  %s
  </body>
  </html>"""
  return base_page % html


class InboxHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return

    query = self.request.get('query', 'in:inbox')
    num_results = self.request.get('numResults', '10')
    search_results = self._service.search(query=query, num_results=num_results)
    html = results_renderer.render(search_results)
    return self.response.out.write(page_html(html))

class FetchWaveHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return
    DIGEST_WAVE_ID = 'googlewave.com!w+SgYrEnoLE'
    wave_id = self.request.get('wave_id', DIGEST_WAVE_ID)
    wave_id = wave_id.replace('%2B', '+')
    wavelet = self._service.fetch_wavelet(wave_id)
    return self.response.out.write(page_html(wave_renderer.render_wavelet(wavelet)));


class MainHandler(webapp.RequestHandler):

  def get(self):
    self.redirect('/app/inbox')

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
