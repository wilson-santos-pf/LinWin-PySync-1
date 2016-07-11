"""
localbox client library
"""

from logging import getLogger

from base64 import b64encode
from base64 import b64decode
from Crypto.Cipher.AES import new as AES_Key
#from Crypto.Cipher.AES import MODE_CBC
from Crypto.Cipher.AES import MODE_CFB
from Crypto.Random import new as CryptoRandom
from os.path import sep

from .gpg import gpg
from .defaults import SITESINI_PATH

try:
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib2 import urlopen
    from urllib import urlencode
    from urllib import quote
    from httplib import BadStatusLine
    from ConfigParser import ConfigParser
except ImportError:
    from urllib.error import HTTPError  # pylint: disable=F0401,E0611
    from urllib.parse import quote  # pylint: disable=F0401,E0611
    from urllib.parse import urlencode  # pylint: disable=F0401,E0611
    from urllib.request import urlopen  # pylint: disable=F0401,E0611
    from urllib.request import Request  # pylint: disable=F0401,E0611
    from http.client import BadStatusLine  # pylint: disable=F0401,E0611
    from configparser import ConfigParser

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
                getLogger(__name__).exception(error.description)
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
                            getLogger(__name__).exception(error)
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
        metapath = quote(path).strip('/')
        request = Request(url=self.url + "lox_api/files/" + metapath)
        data = self._make_call(request).read()
        if self.get_meta(path)['has_keys']:
            data = self.decode_file(path, data)
        return data

    def create_directory(self, path):
        """
        do the create directory call
        """
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/create_folder/',
                          data=metapath)
        try:
            call_result = self._make_call(request)
            if path.count('/') == 1:
                getLogger(__name__).debug("Creating a key for folder " + path)
                key = CryptoRandom().read(16)
                iv = CryptoRandom().read(16)
                self.save_key(path, key, iv)
        except HTTPError as error:
            getLogger(__name__).warning(error)
        # TODO: make directory encrypted

    def delete(self, path):
        """
        do the delete call
        """
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/delete/',
                          data=metapath)
        try:
            return self._make_call(request)
        except HTTPError:
            getLogger(__name__).error("Error remote deleting '%s'", path)

    def upload_file(self, path, localpath):
        """
        upload a file to localbox
        """
        metapath = quote(path)
        contents = open(localpath).read()
        try:
            contents = self.encode_file(path, contents)
        except BadStatusLine as error:
            getLogger(__name__).exception(error)
            # TODO: make sure files get encrypted
        except HTTPError as error:
            getLogger(__name__).exception(error)

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
        try:
            index = path[1:].index('/')
            cryptopath = path[:index + 1]
            getLogger(__name__).exception(
                "call_keys called with a path with excess \"/\"'s.")
        except ValueError:
            cryptopath = path
        getLogger(__name__).debug(
            "call_keys on path %s = %s", (path, cryptopath))

        request = Request(url=self.url + 'lox_api/key/' + cryptopath)
        return self._make_call(request)

    def get_all_users(self):
        request = Request(url=self.url + 'lox_api/identities')
        result = self._make_call(request).read()
        return loads(result)

    def save_key(self, path, key, iv):
        try:
            index = path.index('/')
            cryptopath = path[:index]
            getLogger(__name__).warning(
                "Trying to save a key for an entry in a subdirectory. Saving the key for the subdir instead")
        except ValueError as error:
            cryptopath = path

        site = self.authenticator.label
        location = SITESINI_PATH
        configparser = ConfigParser()
        configparser.read(location)
        user = configparser.get(site, 'user')
        pgpclient = gpg()
        encodedata = {'key': b64encode(pgpclient.encrypt(key, site, user)), 'iv': b64encode(
            pgpclient.encrypt(iv, site, user)), 'user': user}
        data = dumps(encodedata)
        request = Request(
            url=self.url + 'lox_api/key/' + cryptopath, data=data)
        result = self._make_call(request)
        # NOTE: this is just the result of the last call, not all of them.
        # should be more robust then this
        return result

    def decode_file(self, path, contents):
        """
        decode a file
        """
        pgpclient = gpg()
        keydata = loads(self.call_keys(path).read())
        site = self.authenticator.label
        pgpdkeystring = b64decode(keydata['key'])
        pgpdivstring = b64decode(keydata['iv'])
        keystring = pgpclient.decrypt(pgpdkeystring, site)
        ivstring = pgpclient.decrypt(pgpdivstring, site)

        key = AES_Key(keystring, MODE_CFB, ivstring)
        result = key.decrypt(contents)
        return result

    def encode_file(self, path, contents):
        """
        encode a file
        """
        pgpclient = gpg()
        site = self.authenticator.label
        try:
            keydata = loads(self.call_keys(path).read())
            key = pgpclient.decrypt(b64decode(keydata['key']), site)
            iv = pgpclient.decrypt(b64decode(keydata['iv']), site)
        except (HTTPError, TypeError):
            # generate keys if they don't exist
            key = CryptoRandom().read(16)
            iv = CryptoRandom().read(16)
            self.save_key(path, key, iv)
        key = AES_Key(key, MODE_CFB, iv)
        result = key.encrypt(contents)
        return result
