import wsgiref.handlers
import logging
from time import gmtime, strftime

from google.appengine.ext import webapp
from django.utils import simplejson

from waveapi import search
import oauth_handler

class InboxHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return

    query = self.request.get('query', 'in:inbox')
    num_results = self.request.get('numResults', '10')
    search_results = self._service.search(query=query, num_results=num_results)
    html = html_for_results(search_results)
    return self.response.out.write(html)

def results_from_json(json):
    if isinstance(json, basestring):
      json = simplejson.loads(json)
    search_results = search.Results(json['data']['searchResults'])
    return search_results

def html_for_results(results):
    html = '%s, (%s)<br>' % (results.query, results.num_results)
    for digest in results.digests:
      url = 'http://wave.google.com/wave/#restored:wave:%s' % digest.wave_id
      html += '<a href="%s"><b>%s</b></a><br>%s' % (url, digest.title, digest.snippet)
      date = strftime("%a, %d %b %Y %H:%M:%S", gmtime(digest.last_modified/1000))
      html += '%s/%s:%s' % (str(digest.unread_count), str(digest.blip_count),
                            date)
      participants = [p for p in digest.participants]
      html += '(%s)' % ','.join(participants)
      html += '<br><br>'
    return html

class FetchWaveHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return
    wave_id = 'googlewave.com!w+_ZvqGPcnH'
    # digest wave
    #wave_id = 'googlewave.com!w+QH8ZW5LQt'
    wavelet_id = 'googlewave.com!conv+root'
    wave_id = 'googlewave.com!w+0xNca70qA'
    wave_id = 'googlewave.com!w+TNVx0ka5A'
    wave_id = 'googlewave.com!w+vlQQ9rZkC26'
    #wave_id = 'googlewave.com!w%252BQIK8uMFQA'
    wave_id = 'googlewave.com!w+G7ex3qzpA'
    notify_op = "{'id':'0', 'method':'wave.robot.notifyCapabilitiesHash', 'params': {'protocolVersion': '0.21'}}"
    fetch_op = "{'id':'op1', 'method':'wave.robot.fetchWave','params':{'waveId':'%s', 'waveletId': '%s'}}" % (wave_id, wavelet_id)
    data = "[%s, %s]" % (notify_op, fetch_op)
    response = self.perform_operation(data)
    return self.response.out.write(response);

class FolderHandler(oauth_handler.DataRequestHandler):

  def get(self):
    if not self.get_token():
      return
    wave_id = 'googlewave.com!w+_ZvqGPcnH'
    data = "{'id':'op1', 'method':'wave.robot.folderAction','params':{'modifyHow': 'markAsRead', 'waveId':'%s'}}" % (wave_id)
    data = "{'id':'op1', 'method':'wave.robot.folderAction','params':{'waveId':'%s'}}" % (wave_id)
    response = self.perform_operation(data)
    return self.response.out.write(response);

class MainHandler(webapp.RequestHandler):

  def get(self):
    self.response.out.write('<html><head><meta name="google-site-verification" content="qHF5ruQQp1eWXVkXD_B3Q4EzdoSstzZu6_thYkqPPLQ" /></head></html>')

def main():
  application = webapp.WSGIApplication([
                                        ('/', MainHandler),
                                        ('/app/inbox', InboxHandler),
                                        ('/app/fetchwave', FetchWaveHandler),
                                        ('/app/folder', FolderHandler)
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
