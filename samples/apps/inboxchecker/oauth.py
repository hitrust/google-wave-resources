import wsgiref.handlers
import logging
import pickle
import uuid
import httplib
import urllib

from waveapi import oauth

from google.appengine.ext import webapp
from google.appengine.ext import db

REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'
AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'

# example client using httplib with headers
class SimpleOAuthClient(oauth.OAuthClient):

    def __init__(self, server, port=httplib.HTTP_PORT, request_token_url='', access_token_url='', authorization_url=''):
        self.server = server
        self.port = port
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.connection = httplib.HTTPSConnection('www.google.com')

    def fetch_request_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        self.connection.request(oauth_request.http_method, self.request_token_url+'?'+urllib.urlencode(oauth_request.parameters)) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def fetch_access_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        self.connection.request(oauth_request.http_method, self.access_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        # via url
        # -> typically just some okay response
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.getheader('location')#.read()

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


class OAuthHandler(webapp.RequestHandler):
  SIGNATURE_METHOD = oauth.OAuthSignatureMethod.HMAC_SHA1
  SCOPE = 'http://wave.googleusercontent.com/api/rpc'
  COOKIE = 'wavesid'
  CONSUMER_KEY = 'anonymous'
  CONSUMER_SECRET = 'anonymous'

  def __init__(self):
    self._client = SimpleOAuthClient("localhost", 80, REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZATION_URL)
    self._consumer = oauth.OAuthConsumer(OAuthHandler.CONSUMER_KEY, OAuthHandler.CONSUMER_SECRET)


class LoginHandler(OAuthHandler):

  def get(self):
    # Step 1: Fetch Request Token, specifying desired scope
    callback_url = "%s/oauth/verify" % self.request.host_url
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(self._consumer, callback=callback_url, http_url=self._client.request_token_url, parameters = {'scope':OAuthHandler.SCOPE)
    oauth_request.sign_request(OAuthHandler.SIGNATURE_METHOD, self._consumer, None)
    request_token = self._client.fetch_request_token(oauth_request)
    logging.info('Request Token fetched: %s' % request_token)

    # When using HMAC, persist the token secret in order to re-create an
    # OAuthToken object coming back from the approval page.
    db_token = OAuthRequestToken(token_key = request_token.key, token_ser = request_token.to_string())
    db_token.put()

    # Step 2: Generate authorization URL
    oauth_request = oauth.OAuthRequest.from_token_and_callback(token=request_token, http_url=self._client.authorization_url)
    auth_url = client.authorize_token(oauth_request)
    logging.info('Authorization URL: %s' % auth_url)
    # Redirect to URL for authorization
    return self.redirect(auth_url)

class VerifyHandler(OAuthHandler):

  def get(self):
    logging.info(self.request)
    verifier = self.request.get('oauth_verifier')
    token_key = self.request.get('oauth_token')
    # Find request token saved by put() method.
    db_token = OAuthRequestToken.all().filter(
      'token_key =', token_key).fetch(1)[0]
    token = oauth.OAuthToken.from_string(tokenstr)

    # 3.) Exchange the authorized request token for an access token
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(self._consumer, token=token, verifier=verifier, http_url=self._client.access_token_url)
    oauth_request.sign_request(OAuthHandler.SIGNATURE_METHOD, self._consumer, token)
    access_token = self._client.fetch_access_token(oauth_request)

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
