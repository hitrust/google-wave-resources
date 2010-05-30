import wsgiref.handlers
import logging
import pickle
import uuid

from google.appengine.ext import webapp
from google.appengine.ext import db

import gdata
import gdata.service
import atom.http

class OAuthRequestToken(db.Model):
  """Stores OAuth request token."""

  token_key = db.StringProperty(required=True)
  token_secret = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)

class OAuthAccessToken(db.Model):
  """Stores OAuth request token."""

  token_ser = db.TextProperty(required=True)
  token_key = db.StringProperty(required=True)
  token_secret = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  session = db.StringProperty(required=True)


class OAuthHandler(webapp.RequestHandler):
  CONSUMER_KEY = 'anonymous'
  CONSUMER_SECRET = 'anonymous'
  SIGNATURE_METHOD = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
  SCOPE = 'http://wave.googleusercontent.com/api/rpc'
  OAUTH_INPUT_PARAMS = gdata.auth.OAuthInputParams(
                                    SIGNATURE_METHOD,
                                    CONSUMER_KEY,
                                    CONSUMER_SECRET)
  COOKIE = 'wavesid'

  def __init__(self):
    self._service = gdata.service.GDataService()
    self._service.SetOAuthInputParameters(
                                    OAuthHandler.SIGNATURE_METHOD,
                                    OAuthHandler.CONSUMER_KEY,
                                    OAuthHandler.CONSUMER_SECRET)

class LoginHandler(OAuthHandler):

  def get(self):
    callback_url = "%s/oauth/verify" % self.request.host_url
    request_token = self._service.FetchOAuthRequestToken(scopes=OAuthHandler.SCOPE)
    logging.info('Request Token fetched: %s' % request_token)
    self._service.SetOAuthToken(request_token)
    # When using HMAC, persist the token secret in order to re-create an
    # OAuthToken object coming back from the approval page.
    db_token = OAuthRequestToken(token_key = request_token.key,
        token_secret=request_token.secret)
    db_token.put()

    auth_url = self._service.GenerateOAuthAuthorizationURL(callback_url=callback_url)
    logging.info('Authorization URL: %s' % auth_url)
    return self.redirect(auth_url)

class VerifyHandler(OAuthHandler):

  def get(self):
    oauth_token = gdata.auth.OAuthTokenFromUrl(self.request.uri)
    if oauth_token:
      # Find request token saved by put() method.
      db_token = OAuthRequestToken.all().filter(
        'token_key =', oauth_token.key).fetch(1)[0]
      oauth_token.secret = db_token.token_secret
      self._service.SetOAuthToken(oauth_token)

    # 3.) Exchange the authorized request token for an access token
    access_token = self._service.UpgradeToOAuthAccessToken()
    access_token.oauth_input_params = OAuthHandler.OAUTH_INPUT_PARAMS

    session_id = str(uuid.uuid1())
    db_token = OAuthAccessToken(session=session_id, token_key = access_token.key,
        token_secret=access_token.secret, token_ser=pickle.dumps(access_token))
    db_token.put()

    self.response.headers.add_header('Set-Cookie', '%s=%s; path=/;' %
                                     (OAuthHandler.COOKIE, session_id))
    return self.redirect('/data/inbox')


def main():
  application = webapp.WSGIApplication([
                                        ('/oauth/login', LoginHandler),
                                        ('/oauth/verify', VerifyHandler),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
