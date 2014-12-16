'''

Module that implements authentication mechanisms

Usage:

    An authentication module implements both a header and a query part.

The OAuth2 class reads the following parameters from the configuration:

    [session]
    ...
    username=user
    password=userpasswd
    oauth_url=http://localhost/oauth



'''

import config
from error import LoxError
import httplib
import json
import time
import urlparse

class Auth:
    '''
    Abstract class to implement authentication plugins
    '''
    def __init__(self,Name):
        pass
        
    def request(self):
        pass

    def header(self):
        pass
        
    def query(self):
        pass

class OAuth2(Auth):
    '''
    Class (plugin) for OAuth2 authentication
    '''

    client_id = "32yqjbq9u38koggk040w408cccss8og4c0ckso4sgoocwgkkoc" # taken from iOS app
    client_secret = "4j8jqubjrbi8wwsk0ocowooggkc44wcw0044skgscg4o4o44s4" # taken from iOS app

    def __init__(self,Name):
        self.grant_type = "password"
        self.username = config.session(Name)['username']
        self.password = config.session(Name)['password']
        url = config.session(Name)['auth_url']
        o = urlparse.urlparse(url)
        self.uri_path = o.path
        if o.path[-1:]!='/':
            self.uri_path +='/'
        if o.scheme == 'https':
            self.connection = httplib.HTTPSConnection(o.netloc,o.port)
        elif o.scheme == 'http' or o.scheme=='':
            self.connection = httplib.HTTPConnection(o.netloc,o.port)
        self.access_token = ""
        self.token_expires = 0

    def _request(self):
        url =self.uri_path
        url += "token"
        url += "?grant_type="+self.grant_type
        url += "&client_id="+self.client_id
        url += "&client_secret="+self.client_secret
        url += "&username="+self.username
        url += "&password="+self.password
        self.connection.request("GET",url)
        resp = self.connection.getresponse()
        if resp.status == 200:
            data = json.loads(resp.read())
            self.access_token = str(data[u'access_token'])
            self.token_expires = time.time() + data[u'expires_in'] - 10 # invalidate 10 seconds before
        else:
            raise LoxError("Authentication failed, "+resp.reason)

    def header(self):
        if time.time() > self.token_expires:
            self._request()
        #else:
            #t = str(self.token_expires-time.time())
            #TODO: figure out what the plan with this was
        return {"Authorization": "Bearer "+self.access_token}

    def query(self):
        "access_token="+self.access_token
