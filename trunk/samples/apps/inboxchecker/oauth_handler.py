import wsgiref.handlers
import logging
import pickle
import uuid
import httplib

from google.appengine.ext import webapp
from google.appengine.ext import db

from waveapi import oauth
from waveapi import wavelet
from waveapi import waveservice


class OAuthRequestToken(db.Model):
  """Stores OAuth request token."""

  token_key = db.StringProperty(required=True)
  token_secret = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  token_ser = db.TextProperty()

class OAuthAccessToken(db.Model):
  """Stores OAuth request token."""

  token_ser = db.TextProperty(required=True)
  token_key = db.StringProperty(required=True)
  token_secret = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  session = db.StringProperty(required=True)


class WaveOAuthHandler(webapp.RequestHandler):
  COOKIE = 'wavesid'

  def __init__(self):
    self._service = waveservice.WaveService()


class LoginHandler(WaveOAuthHandler):

  def get(self):
    # Step 1: Fetch request token, specifying callback
    callback_url = "%s/oauth/verify" % self.request.host_url
    request_token = self._service.fetch_request_token(callback=callback_url)
    logging.info('Request Token fetched: %s' % request_token)

    # Persist the token secret in order to re-create an
    # OAuthToken object coming back from the approval page.
    db_token = OAuthRequestToken(token_key = request_token.key, token_ser = request_token.to_string())
    db_token.put()

    # Step 2: Generate authorization URL and redirect
    auth_url = self._service.generate_authorization_url()
    logging.info('Authorization URL: %s' % auth_url)
    return self.redirect(auth_url)

class VerifyHandler(WaveOAuthHandler):

  def get(self):
    token_key = self.request.get('oauth_token')
    verifier = self.request.get('oauth_verifier')
    # Find request token saved by put() method.
    db_token = OAuthRequestToken.all().filter(
      'token_key =', token_key).fetch(1)[0]
    token = oauth.OAuthToken.from_string(db_token.token_ser)

    # Step 3: Exchange the authorized request token for an access token
    access_token = self._service.upgrade_to_access_token(request_token=token,
                                                         verifier=verifier)

    # Store a session ID for this user, & relate token to session ID in datastore
    session_id = str(uuid.uuid1())
    db_token = OAuthAccessToken(session=session_id, token_key = access_token.key,
        token_secret=access_token.secret, token_ser=access_token.to_string())
    db_token.put()

    self.response.headers.add_header('Set-Cookie', '%s=%s; path=/;' %
                                     (WaveOAuthHandler.COOKIE, session_id))
    return self.redirect('/app/inbox')

class DataRequestHandler(WaveOAuthHandler):

  def get_token(self):
    session_id = self.request.cookies.get(WaveOAuthHandler.COOKIE)
    if not session_id:
      logging.info('Found no session ID cookie')
      return self.redirect('/oauth/login')
    db_query = OAuthAccessToken.all().filter('session =', session_id)
    db_token = db_query.get()
    if db_token is None:
      logging.info('Found no matching token for session ID')
      return self.redirect('/oauth/login')
    self._service.set_access_token(db_token.token_ser)
    return True

def main():
  application = webapp.WSGIApplication([
                                        ('/oauth/login', LoginHandler),
                                        ('/oauth/verify', VerifyHandler),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
