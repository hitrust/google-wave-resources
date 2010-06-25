import wsgiref.handlers
import logging
import string
from time import gmtime, strftime

from google.appengine.ext import webapp
from django.utils import simplejson

from waveapi import search
import oauth_handler
import blipconverter

def results_from_json(json):
    if isinstance(json, basestring):
      json = simplejson.loads(json)
    search_results = search.Results(json['data']['searchResults'])
    return search_results

def html_for_results(results):
    html = '%s, (%s)<br>' % (results.query, results.num_results)
    for digest in results.digests:
      url = 'http://wave.google.com/wave/#restored:wave:%s' % digest.wave_id
      url = '/app/fetchwave?wave_id=%s' % digest.wave_id.replace('+', '%252B')
      html += '<a href="%s"><b>%s</b></a><br>%s' % (url, digest.title, digest.snippet)
      date = strftime("%a, %d %b %Y %H:%M:%S", gmtime(digest.last_modified/1000))
      html += '%s/%s:%s' % (str(digest.unread_count), str(digest.blip_count),
                            date)
      participants = [p for p in digest.participants]
      html += '(%s)' % ','.join(participants)
      html += '<br><br>'
    return html

def html_for_wavelet(wavelet):
  html_list = []
  for blip_id in wavelet.blips:
    blip = wavelet.blips.get(blip_id)
    html_list.append(blipconverter.ToHTML(blip))
  return string.join(html_list, '<br><br>')

class InboxHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return

    query = self.request.get('query', 'in:inbox')
    num_results = self.request.get('numResults', '10')
    search_results = self._service.search(query=query, num_results=num_results)
    html = html_for_results(search_results)
    return self.response.out.write(html)

class FetchWaveHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return
    DIGEST_WAVE_ID = 'googlewave.com!w+SgYrEnoLE'
    wave_id = self.request.get('wave_id', DIGEST_WAVE_ID)
    wave_id = wave_id.replace('%2B', '+')
    wavelet = self._service.fetch_wavelet(wave_id, 'googlewave.com!conv+root')
    return self.response.out.write(html_for_wavelet(wavelet));

class MainHandler(webapp.RequestHandler):

  def get(self):
    self.response.out.write('<html><head><meta name="google-site-verification" content="qHF5ruQQp1eWXVkXD_B3Q4EzdoSstzZu6_thYkqPPLQ" /></head></html>')

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
