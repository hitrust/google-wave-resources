import httplib
import urllib

from waveapi import oauth

class GoogleOAuthClient(oauth.OAuthClient):
  REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
  ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'
  AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'

  def __init__(self, server, port=httplib.HTTP_PORT,
               request_token_url=REQUEST_TOKEN_URL,
               access_token_url=ACCESS_TOKEN_URL,
               authorization_url=AUTHORIZATION_URL):
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
    return response.getheader('location')
