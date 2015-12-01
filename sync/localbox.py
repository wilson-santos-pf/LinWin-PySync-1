"""
localbox client library
"""
try:
    from urllib2 import urlopen
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib import urlencode
    from urllib import quote
except ImportError:
    from urllib import quote
    from urllib.request import urlopen # pylint: disable=F0401,E0611
    from urllib.request import Request # pylint: disable=F0401,E0611
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
            return self.authentication_url
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
                        except ValueError:
                            bearer = False
                    if field.lower() == 'bearer':
                        bearer = True
        raise AlreadyAuthenticatedError()

    def _make_call(self, request):
        request.add_header('Authorization', self.authenticator.get_authorization_header())
        return urlopen(request)

    def get_meta(self, path=''):
        metapath = quote(path)
        request = Request(url=self.url + "lox_api/meta" + metapath)
        json_text = self._make_call(request).read()
        return loads(json_text)

    def get_file(self, path=''):
        metapath = quote(path)
        request = Request(url=self.url + 'lox_api/files' + metapath)
        return self._make_call(request).read()

    def create_directory(self, path):
        if path[0] != '/':
            path = '/' + path
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/create_folder/', data=metapath)
        return self._make_call(request)

    def delete(self, path):
        if path[0] != '/':
            path = '/' + path
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/delete/', data=metapath)

    def upload_file(self, path, localpath):
        if path[0] == '.':
            path = path[1:]
        if len(path) > 0 and path[0] == '/':
            path = path[1:]
        metapath = quote(path)
        print metapath
        contents = open(localpath).read()
        request = Request(url=self.url + 'lox_api/files/' + metapath, data=contents) 
        return self._make_call(request)





