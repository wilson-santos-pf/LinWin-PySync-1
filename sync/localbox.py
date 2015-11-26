"""
localbox client library
"""
from pprint import pprint 
try:
    from urllib2 import urlopen
    from urllib2 import HTTPError
    from urllib2 import HTTPHandler
    from urllib2 import Request
    from urllib import quote
except ImportError:
    from urllib import quote
    from urllib.request import urlopen # pylint: disable=F0401,E0611
    from urllib.request import Request # pylint: disable=F0401,E0611
    from urllib.request import HTTPHandler # pylint: disable=F0401,E0611
    from urllib.error import HTTPError # pylint: disable=F0401,E0611
from json import loads


class AlreadyAuthenticatedError(Exception):
    pass


class LocalBox(object):
    def __init__(self, url):
        self.url = url
        self.authentication_url = None
        self.authenticator = None

    def add_authenticator(self, authenticator):
        self.authenticator = authenticator

    def get_authentication_url(self):
        if self.authentication_url != None:
            return authentication_url
        else:
            try:
                urlopen(self.url)
            except HTTPError as error:
                auth_header = error.headers['WWW-Authenticate'].split(' ')
                bearer = False
                for field in auth_header:
                    if bearer:
                        try:
                            entry = field.split('=', 1)
                            if entry[0].lower() == "domain":
                                return entry[1][1:-1]
                        except ValueError as e:
                            bearer = False
                    if field.lower() == 'bearer':
                        bearer = True
        raise AlreadyAuthenticatedError()

    def make_call(self, request):
        request.add_header('Authorization', self.authenticator.get_authorization_header())
        return urlopen(request)

    def get_meta(self, path=''):
        metapath = quote(path)
        request = Request(url=self.url + "lox_api/meta" + metapath)
        json_text = self.make_call(request).read()
        return loads(json_text)


