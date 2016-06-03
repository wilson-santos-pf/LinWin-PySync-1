"""
localbox client library
"""

from logging import getLogger

from Crypto.Cipher.AES import new as AES_Key
from Crypto.Cipher.AES import MODE_CBC

try:
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib2 import urlopen
    from urllib import urlencode
    from urllib import quote
    from httplib import BadStatusLine
except ImportError:
    from urllib.error import HTTPError  # pylint: disable=F0401,E0611
    from urllib.parse import quote  # pylint: disable=F0401,E0611
    from urllib.parse import urlencode  # pylint: disable=F0401,E0611
    from urllib.request import urlopen  # pylint: disable=F0401,E0611
    from urllib.request import Request  # pylint: disable=F0401,E0611
    from http.client import BadStatusLine  # pylint: disable=F0401,E0611

from json import loads
from json import dumps
from ssl import SSLContext, PROTOCOL_TLSv1  # pylint: disable=E0611


class AlreadyAuthenticatedError(Exception):

    """
    authentication has already been done error.
    """
    pass


class LocalBox(object):

    """
    object representing localbox
    """

    def __init__(self, url):
        if url[-1] != '/':
            url = url + "/"
        self.url = url
        self.authentication_url = None
        self.authenticator = None

    def add_authenticator(self, authenticator):
        """
        add an authenticator to the localbox to do authenticationwhen needed
        """
        self.authenticator = authenticator

    def get_authentication_url(self):
        """
        return an authentication url belonging to a localbox instance.
        """
        if self.authentication_url is not None:
            return self.authentication_url
        else:
            try:
                non_verifying_context = SSLContext(PROTOCOL_TLSv1)
                urlopen(self.url, context=non_verifying_context)
            except BadStatusLine as error:
                getLogger('error').exception(error.description)
                raise error
            except HTTPError as error:
                if error.code != 401:
                    raise error
                auth_header = error.headers['WWW-Authenticate'].split(' ')
                bearer = False
                for field in auth_header:
                    if bearer:
                        try:
                            entry = field.split('=', 1)
                            if entry[0].lower() == "domain":
                                return entry[1][1:-1]
                        except ValueError as error:
                            getLogger('error').exception(error)
                            bearer = False
                    if field.lower() == 'bearer':
                        bearer = True
        raise AlreadyAuthenticatedError()

    def _make_call(self, request):
        """
        do the actual call to the server with authentication data
        """
        request.add_header('Authorization',
                           self.authenticator.get_authorization_header())
        non_verifying_context = SSLContext(PROTOCOL_TLSv1)
        return urlopen(request, context=non_verifying_context)

    def get_meta(self, path=''):
        """
        do the meta call
        """
        metapath = quote(path).strip('/')
        request = Request(url=self.url + "lox_api/meta/" + metapath)
        json_text = self._make_call(request).read()
        return loads(json_text)

    def get_file(self, path=''):
        """
        do the file call
        """
        data = self._make_call(request).read()
        if self.get_meta(path)['has_keys']:
            data = self.decode_file(path, data)
        return data

    def create_directory(self, path):
        """
        do the create directory call
        """
        if path[0] != '/':
            path = '/' + path
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/create_folder/',
                          data=metapath)
        try:
            return self._make_call(request)
        except HTTPError as error:
            print "Problem creating directory"
        # TODO: make directory encrypted

    def delete(self, path):
        """
        do the delete call
        """
        if path[0] != '/':
            path = '/' + path
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/delete/',
                          data=metapath)
        return self._make_call(request)

    def upload_file(self, path, localpath):
        """
        upload a file to localbox
        """
        if path[0] == '.':
            path = path[1:]
        if len(path) > 0 and path[0] == '/':
            path = path[1:]
        metapath = quote(path)
        contents = open(localpath).read()
        try:
            if self.get_meta(path)['has_keys']:
                contents = self.encode_file(path, contents)
        except BadStatusLine as error:
            getLogger('error').exception(error)
            # TODO: make sure files get encrypted
        except HTTPError as error:
            getLogger('error').exception(error)

        request = Request(url=self.url + 'lox_api/files/' + metapath,
                          data=contents)
        return self._make_call(request)

    def call_user(self, send_data=None):
        """
        do the user call
        """
        url = self.url + "lox_api/user"
        if send_data is None:
            request = Request(url)
        else:
            request = Request(url, data=send_data)
        return self._make_call(request)

    def call_keys(self, path):
        """
        do the keys call
        """
        if path[0] == '.':
            path = path[1:]
        if len(path) > 0 and path[0] == '/':
            path = path[1:]
        try:
            index = path.index('/')
            cryptopath = path[:index]
        except ValueError as error:
            getLogger('error').exception(error)
            cryptopath = path
        request = Request(url=self.url + 'lox_api/key/' + cryptopath)
        return self._make_call(request)

    def save_key(self, path, key, iv):
        if path[0] == '.':
            path = path[1:]
        if len(path) > 0 and path[0] == '/':
            path = path[1:]
        try:
            index = path.index('/')
            cryptopath = path[:index]
        except ValueError as error:
            getLogger('error').exception(error)
            cryptopath = path

        data = urlencode({'key': key, 'iv': iv})
        request = Request(
            url=self.url + 'lox_api/key/' + cryptopath, data=data)
        return self._make_call(request)

    def decode_file(self, path, contents):
        """
        decode a file
        """
        keydata = loads(self.call_keys(path))
        key = AES_Key(keydata['key'], MODE_CBC, keydata['iv'])
        key.decrypt(contents)
        return contents

    def encode_file(self, path, contents):
        """
        encode a file
        """
        keydata = loads(self.call_keys(path))
        key = AES_Key(keydata['key'], MODE_CBC, keydata['iv'])
        key.encrypt(contents)
        return contents
