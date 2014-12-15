'''

Module that implements communication with a LocalBox store

Usage: create an instance per account


'''

import lox.config
import lox.auth
from lox.error import LoxError
import httplib
import urllib
import json
import time
import urlparse

class Api:
    '''
    Class that forms the API to a LocalBox store.
    Each instance containts its own HTTP(S)Connection, can be used to
    manage multiple connections.
    API calls are based on version 1.1.3
    '''

    def __init__(self,Name):
        authtype = lox.config.session(Name)['auth_type']
        if authtype.lower() == 'oauth2':
            self.auth = lox.auth.OAuth2(Name)
        else:
            raise LoxError('not supported')
        self.agent = {"Agent":"lox-client"} # use one time generated UUID in the future?
        url = lox.config.session(Name)['lox_url']
        o = urlparse.urlparse(url)
        self.uri_path = o.path
        if o.path[-1:]!='/':
            self.uri_path +='/'
        if o.scheme == 'https':
            self.connection = httplib.HTTPSConnection(o.netloc,o.port)
        elif o.scheme == 'http' or o.scheme=='':
            self.connection = httplib.HTTPConnection(o.netloc,o.port)

    def identities(self,Begin):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/identities/"+Begin
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
        else:
            raise LoxError(resp.reason)

    def user_info(self):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/user"
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
        else:
            raise LoxError(resp.reason)

    def meta(self,path):
        #print "meta("+path+")"
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/meta/"+urllib.pathname2url(path)
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
        else:
            raise LoxError(resp.reason)

    def upload(self,path,content_type,body):
        headers = self.auth.header()
        headers.update(self.agent)
        headers.update({"Content-Type":content_type})
        url = self.uri_path
        url += "lox_api/files"+urllib.pathname2url(path)
        self.connection.request("POST",url,body,headers)
        resp = self.connection.getresponse()
        if resp.status != 200:
            raise LoxError(resp.reason)

    def download(self,path):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/files/"+urllib.pathname2url(path)
        print url
        print headers
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return resp.read()
        else:
            raise LoxError(resp.reason)

    def create_folder(self,path):
        headers = self.auth.header()
        headers.update(self.agent)
        headers.update({"Content-Type":"application/x-www-form-urlencoded"})
        url = self.uri_path
        url += "lox_api/operations/create_folder"
        body = "path="+urllib.pathname2url(path)
        self.connection.request("POST",url,body,headers)
        resp = self.connection.getresponse()
        if resp.status != 200:
            raise LoxError(resp.reason)

    def delete(self,path):
        headers = self.auth.header()
        headers.update(self.agent)
        headers.update({"Content-Type":"application/x-www-form-urlencoded"})
        url = self.uri_path
        url += "lox_api/operations/delete"
        body = "path="+urllib.pathname2url(path)
        self.connection.request("POST",url,body,headers)
        resp = self.connection.getresponse()
        if resp.status != 200:
            raise LoxError(resp.reason)

    def get_key(self,path):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/key/"+urllib.pathname2url(path)
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
        else:
            raise LoxError(resp.reason)

    def set_key(self,path,user,key,iv):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/key/"+urllib.pathname2url(path)
        body = json.dumps({'username':user,'key':key,'iv':iv})
        self.connection.request("POST",url,body,headers)
        resp = self.connection.getresponse()
        if resp.status != 200:
            raise LoxError(resp.reason)

    def key_revoke(self,path,user):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/key_revoke/"+urllib.pathname2url (path)
        body = json.dumps({'username':user})
        self.connection.request("POST",url,body,headers)
        resp = self.connection.getresponse()
        if resp.status != 200:
            raise LoxError(resp.reason)

    def invitations(self):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/invitations"
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status != 200:
            raise LoxError(resp.reason)

    def invite_accept(self,ref):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/invite/"+ref+"/accept"
        self.connection.request("POST",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
        else:
            raise LoxError(resp.reason)

    def invite_revoke(self,ref):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "lox_api/invite/"+ref+"/revoke"
        self.connection.request("POST",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return resp.read()
        else:
            raise LoxError(resp.reason)

    def notifications(self):
        headers = self.auth.header()
        headers.update(self.agent)
        url = self.uri_path
        url += "notifications/unread/"
        headers.update({"X-Requested-With":"XMLHttpRequest"})
        self.connection.request("GET",url,"",headers)
        resp = self.connection.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
        else:
            raise LoxError(resp.reason)

