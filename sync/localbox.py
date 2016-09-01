"""
localbox client library
"""

from logging import getLogger
from md5 import new as newmd5

from base64 import b64encode
from base64 import b64decode
from Crypto.Cipher.AES import new as AES_Key
from Crypto.Cipher.AES import MODE_CFB
from Crypto.Random import new as CryptoRandom

from .gpg import gpg
from .defaults import SITESINI_PATH
from os import stat

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
    from configparser import ConfigParser  # pylint: disable=F0401,E0611

from os import fsync
from json import loads
from json import dumps
from ssl import SSLContext, PROTOCOL_TLSv1  # pylint: disable=E0611


def getChecksum(key):
    """
    returns a partial hash of the given key for differentiation in logs. May need a stronger algorithm.
    """
    checksum = newmd5()
    checksum.update(key)
    return checksum.hexdigest()[:5]


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
        getLogger(__name__).debug("initialising Localbox for %s", url)
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
        webdata = self._make_call(request)
        websize = webdata.headers.get('content-length', -1)
        data = webdata.read()
        ldata = len(data)
        stats = self.get_meta(path)
        if stats['has_keys']:
            data = self.decode_file(path, data)

        getLogger(__name__).info("Downloading %s: Websize: %d, readsize: %d cryptosize: %d", path, websize, ldata, len(data))

        return data

    def create_directory(self, path):
        """
        do the create directory call
        """
        metapath = urlencode({'path': path})
        request = Request(url=self.url + 'lox_api/operations/create_folder/',
                          data=metapath)
        try:
            self._make_call(request)
            if path.count('/') == 1:
                getLogger(__name__).debug("Creating a key for folder " + path)
                key = CryptoRandom().read(16)
                iv = CryptoRandom().read(16)
                self.save_key(path, key, iv)
        except HTTPError as error:
            getLogger(__name__).warning("'%s' whilst creating directory %s", error, path)
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
        #contents = open(localpath).read()
        #larger version
        stats = stat(localpath)
        openfile = open(localpath, 'rb')
        contents = openfile.read(stats.st_size)
        openfile.flush()
        clen = len(contents)
        try:
            contents = self.encode_file(path, contents)
        except BadStatusLine as error:
            getLogger(__name__).exception(error)
            # TODO: make sure files get encrypted
        except HTTPError as error:
            getLogger(__name__).exception(error)

        getLogger(__name__).info("Uploading %s: Statsize: %d, readsize: %d cryptosize: %d", localpath, stats.st_size, clen, len(contents))

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
            cryptopath = path[1:index + 1]
            getLogger(__name__).exception(
                "call_keys called with a path with excess \"/\"'s: %s", path)
        except ValueError:
            cryptopath = path[1:]
        getLogger(__name__).debug(
            "call_keys on path %s = %s", path, cryptopath)

        request = Request(url=self.url + 'lox_api/key/' + cryptopath)
        return self._make_call(request)

    def get_all_users(self):
        """
        gets a list from the localbox server with all users.
        """
        request = Request(url=self.url + 'lox_api/identities')
        result = self._make_call(request).read()
        return loads(result)


    def save_key(self, path, key, iv):
        """
        saves an encrypted key on the localbox server
        """
        try:
            index = path[1:].index('/')
            cryptopath = path[1:index + 1]
            getLogger(__name__).warning(
                "Trying to save a key for an entry in a subdirectory. Saving the key for the subdir instead")
        except ValueError:
            cryptopath = path[1:]
        
        cryptopath=quote(cryptopath)
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
        getLogger(__name__).debug('saving key for %s', cryptopath)
        # NOTE: this is just the result of the last call, not all of them.
        # should be more robust then this
        return result


    def decode_file(self, path, contents):
        """
        decode a file
        """
        path = quote(path)
        pgpclient = gpg()
        site = self.authenticator.label
        try:
          jsontext = self.call_keys(path).read()
          keydata = loads(jsontext)
          pgpdkeystring = b64decode(keydata['key'])
          pgpdivstring = b64decode(keydata['iv'])
          keystring = pgpclient.decrypt(pgpdkeystring, site)
          ivstring = pgpclient.decrypt(pgpdivstring, site)

          getLogger(__name__).debug("Decoding %s with key %s", path, getChecksum(keystring))
          key = AES_Key(keystring, MODE_CFB, ivstring)
          result = key.decrypt(contents)
        except ValueError:
          getLogger(__name__).info("cannot decode JSON: %s", jsontext)
          result = None
        except HTTPError as error:
          getLogger(__name__).info("HTTPError: %s", error)
          result = None
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
        except (HTTPError, TypeError, ValueError):
            getLogger(__name__).debug("path '%s' is without key, generating one.", path)
            # generate keys if they don't exist
            key = CryptoRandom().read(16)
            iv = CryptoRandom().read(16)
            self.save_key(path, key, iv)
        getLogger(__name__).debug("Encoding %s with key %s", path, getChecksum(key))
        key = AES_Key(key, MODE_CFB, iv)
        result = key.encrypt(contents)
        return result
