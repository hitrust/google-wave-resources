import wsgiref.handlers
import logging
import pickle
import uuid

from google.appengine.ext import webapp
from google.appengine.ext import db
from django.utils import simplejson

import gdata
import atom.http
from waveapi import search
import oauth

class DataRequestHandler(oauth.OAuthHandler):

  def get_token(self):
    session_id = self.request.cookies.get(oauth.OAuthHandler.COOKIE)
    if not session_id:
      logging.info('Found no session ID cookie')
      return self.redirect('/oauth/login')
    db_query = oauth.OAuthAccessToken.all().filter('session =', session_id)
    db_token = db_query.get()
    if db_token is None:
      logging.info('Found no matching token for session ID')
      return self.redirect('/oauth/login')
    self._access_token = gdata.auth.OAuthToken(db_token.token_key, db_token.token_secret,
                                         scopes=oauth.OAuthHandler.SCOPE,
                                         oauth_input_params=oauth.OAuthHandler.OAUTH_INPUT_PARAMS)
    return True

  def make_request(self, data):
    url = 'https://www-opensocial.googleusercontent.com/api/rpc'
    client = atom.http.ProxiedHttpClient()
    response = self._access_token.perform_request(client, 'POST',
                                              url, data,
                                              headers={'Content-Type':'application/json'})
    return response

class InboxHandler(DataRequestHandler):

  def get(self):
    if not self.get_token():
      return
    data = "{'id':'op1','method':'wave.robot.search','params':{'query':'in:inbox'}}"
    response = self.make_request(data)
    search_results = results_from_json(response.read())
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
      participants = [p for p in digest.participants]
      html += '(%s)' % ','.join(participants)
      html += '<br><br>'
    return html

def main():
  application = webapp.WSGIApplication([
                                        ('/data/inbox', InboxHandler)
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
