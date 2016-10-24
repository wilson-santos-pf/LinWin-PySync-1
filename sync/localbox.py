"""
localbox client library
"""

import os
import errno
import hashlib
import urllib
from Crypto.Cipher.AES import MODE_CFB
from Crypto.Cipher.AES import new as AES_Key
from Crypto.Random import new as CryptoRandom
from base64 import b64decode
from base64 import b64encode
from logging import getLogger
from md5 import new as newmd5
from os import stat, remove
from socket import error as SocketError

from sync import defaults
from sync.auth import Authenticator, AlreadyAuthenticatedError
from sync.controllers.localbox_ctrl import SyncsController
from sync.gpg import gpg

try:
    from urllib2 import HTTPError, URLError
    from urllib2 import Request
    from urllib2 import urlopen
    from urllib import urlencode
    from urllib import quote_plus
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


class LocalBox(object):
    """
    object representing localbox
    """

    def __init__(self, url, label):
        if url[-1] != '/':
            url += "/"
        self.url = url
        self._authentication_url = None
        self._authentication_url = self.get_authentication_url()
        self._authenticator = Authenticator(self._authentication_url, label)

    @property
    def authenticator(self):
        return self._authenticator

    def get_authentication_url(self):
        """
        return an authentication url belonging to a localbox instance.
        """
        if self._authentication_url is not None:
            return self._authentication_url
        else:
            try:
                non_verifying_context = SSLContext(PROTOCOL_TLSv1)
                getLogger(__name__).debug("validating localbox server: %s" % self.url)
                urlopen(self.url, context=non_verifying_context)
            except BadStatusLine as error:
                getLogger(__name__).exception(error)
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
        metapath = quote_plus(path)
        request = Request(url=self.url + 'lox_api/meta', data=dumps({'path': path}))
        getLogger(__name__).debug('calling lox_api/meta for path: %s' % metapath)
        json_text = self._make_call(request).read()
        return loads(json_text)

    def get_file(self, path=''):
        """
        do the file call
        """
        metapath = quote_plus(path).strip('/')
        request = Request(url=self.url + "lox_api/files", data=dumps({'path': metapath}))
        webdata = self._make_call(request)
        websize = webdata.headers.get('content-length', -1)
        data = webdata.read()
        ldata = len(data)
        getLogger(__name__).info("Downloaded %s: Websize: %d, readsize: %d cryptosize: %d", path, websize, ldata,
                                 len(data))
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
            getLogger(__name__).warning("'%s' whilst creating directory %s. %s", error, path, error.message)
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

    def upload_file(self, path, localpath, passphrase):
        """
        upload a file to localbox
        """
        metapath = quote_plus(path)
        # contents = open(localpath).read()
        # larger version
        stats = stat(localpath)
        openfile = open(localpath, 'rb')
        contents = openfile.read(stats.st_size)
        openfile.flush()

        try:
            contents = gpg.add_pkcs7_padding(contents)
            clen = len(contents)
            contents = self.encode_file(path, contents, passphrase)
        except BadStatusLine as error:
            getLogger(__name__).exception(error)
            # TODO: make sure files get encrypted
        except HTTPError as error:
            getLogger(__name__).exception(error)

        # remove plain file and save encryted
        openfile.close()
        try:
            remove(localpath)
        except Exception as error:
            getLogger(__name__).error('Failed to remove decrypted file: %s, %s' % (localpath, error))

        encrypted_file = open(localpath + defaults.LOCALBOX_EXTENSION, 'wb')
        encrypted_file.write(contents)
        encrypted_file.close()

        getLogger(__name__).info("Uploading %s: Statsize: %d, readsize: %d cryptosize: %d", localpath, stats.st_size,
                                 clen, len(contents))

        request = Request(url=self.url + 'lox_api/files',
                          data=dumps({'contents': b64encode(contents), 'path': metapath}))
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
        # try:
        #     index = path[1:].index('/')
        #     cryptopath = path[1:index + 1]
        # except ValueError:
        #     getLogger(__name__).exception("call_keys called with a path with excess \"/\"'s: %s", path)
        #     cryptopath = path[1:]
        keys_path = LocalBox.get_keys_path(path)
        keys_path = urllib.quote_plus(keys_path)
        getLogger(__name__).debug("call lox_api/key on path %s = %s", path, keys_path)

        request = Request(url=self.url + 'lox_api/key/' + keys_path)
        return self._make_call(request)

    def call_create_share(self):
        request = Request(url=self.url + 'lox_api/create_share/' + keys_path, data=data)
        return self._make_call(request)


    @staticmethod
    def get_keys_path_v2(localbox_path):
        """
        Get the keys location for this localbox path.

        >>> LocalBox.get_keys_path('/a/b/c')
        'a/b'
        >>> LocalBox.get_keys_path('a')
        'a'
        >>> LocalBox.get_keys_path('/a/b/c/')
        'a/b/c'
        >>> LocalBox.get_keys_path('a/b')
        'a'

        :param localbox_path:
        :return: it returns the parent 'directory'
        """
        slash_count = localbox_path.count('/')
        if slash_count > 1:
            keys_path = os.path.dirname(localbox_path).lstrip('/')
        elif slash_count == 1 and localbox_path.index('/') > 0:
            keys_path = os.path.dirname(localbox_path).lstrip('/')
        else:
            keys_path = localbox_path

        getLogger(__name__).debug('keys_path for localbox_path "%s" is "%s"' % (localbox_path, keys_path))
        return keys_path

    @staticmethod
    def get_keys_path(localbox_path):
        """
        Get the keys location for this localbox path.

        >>> LocalBox.get_keys_path('/a/b/c')
        'a'
        >>> LocalBox.get_keys_path('a')
        'a'
        >>> LocalBox.get_keys_path('/a/b/c/')
        'a'
        >>> LocalBox.get_keys_path('a/b')
        'a'

        :param localbox_path:
        :return: it returns the parent 'directory'
        """
        if localbox_path.startswith('/'):
            localbox_path = localbox_path[1:]

        keys_path = localbox_path.split('/')[0]

        getLogger(__name__).debug('keys_path for localbox_path "%s" is "%s"' % (localbox_path, keys_path))
        return keys_path

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
        # try:
        #     index = path[1:].index('/')
        #     cryptopath = path[1:index + 1]
        #     getLogger(__name__).warning(
        #         "Trying to save a key for an entry in a subdirectory. Saving the key for the subdir instead")
        # except ValueError:
        #     cryptopath = path[1:]
        cryptopath = LocalBox.get_keys_path(path)
        cryptopath = quote_plus(cryptopath)

        site = self.authenticator.label
        ctrl = SyncsController()
        user = ctrl.get(site).user
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

    def decode_file(self, path, filename, passphrase):
        """
        decode a file
        """
        try:
            path = path.replace('\\', '/')
            stats = self.get_meta(path)
            if stats['has_keys']:
                pgpclient = gpg()

                # call the backend to get rsa encrypted key and initialization vector for decoding the file
                jsontext = self.call_keys(path).read()
                keydata = loads(jsontext)

                pgpdkeystring = b64decode(keydata['key'])
                pgpdivstring = b64decode(keydata['iv'])

                keystring = pgpclient.decrypt(pgpdkeystring, passphrase)
                ivstring = pgpclient.decrypt(pgpdivstring, passphrase)

                try:
                    getLogger(__name__).debug('Decoding "%s" with key "%s"', path, getChecksum(keystring))
                    key = AES_Key(keystring, MODE_CFB, ivstring, segment_size=128)
                except ValueError:
                    getLogger(__name__).info("cannot decode JSON: %s", jsontext)
                    return None

                with open(filename, 'rb') as content_file:
                    contents = content_file.read()
                    result = key.decrypt(contents)

                return gpg.remove_pkcs7_padding(result)
            else:
                getLogger(__name__).error("No keys found for %s", path)
                return None
        except HTTPError as error:
            getLogger(__name__).info("HTTPError: %s", error)
            return None

    def encode_file(self, path, contents, passphrase):
        """
        encode a file
        """
        pgpclient = gpg()
        try:
            keydata = loads(self.call_keys(path).read())
            key = pgpclient.decrypt(b64decode(keydata['key']), passphrase)
            iv = pgpclient.decrypt(b64decode(keydata['iv']), passphrase)
        except (HTTPError, TypeError, ValueError):
            getLogger(__name__).debug("path '%s' is without key, generating one.", path)
            # generate keys if they don't exist
            key = CryptoRandom().read(16)
            iv = CryptoRandom().read(16)
            self.save_key(path, key, iv)
        getLogger(__name__).debug("Encoding %s with key %s", path, getChecksum(key))
        key = AES_Key(key, MODE_CFB, iv, segment_size=128)
        result = key.encrypt(contents)
        return result

    def is_valid_url(self):
        getLogger(__name__).debug("validating localbox server: %s" % (self.url))
        try:
            self.get_authentication_url()
            return True
        except (URLError, BadStatusLine, ValueError,
                AlreadyAuthenticatedError) as error:
            getLogger(__name__).debug("error with authentication url thingie")
            getLogger(__name__).exception(error)
            return False
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                raise  # Not error we are looking for
            getLogger(__name__).error('Failed to connect to server, maybe forgot https? %s', e)
            return False


class InvalidLocalboxError(Exception):
    """
    URL for localbox backend is invalid or is unreachable
    """
    pass


if __name__ == "__main__":
    import doctest

    doctest.testmod()
