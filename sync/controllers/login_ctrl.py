import json
try:
    import urllib2 as urllib
except:
    import urllib
from logging import getLogger

from sync.gpg import gpg


class LoginController(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LoginController, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, '_passphrase'):
            self._logged_in = False
            self._passphrase = dict()

    def store_keys(self, localbox_client, pubkey, privkey, passphrase):
        username = localbox_client.authenticator.username
        site = localbox_client.label
        # set up gpg
        keys = gpg()
        if pubkey is not None and privkey is not None:
            getLogger(__name__).debug("private key found and public key found")

            result = keys.add_keypair(pubkey,
                                      privkey,
                                      site,
                                      username,
                                      passphrase)
            if result is None:
                getLogger(__name__).debug("could not add keypair")
        else:
            getLogger(__name__).debug("public keys not found. generating...")
            fingerprint = keys.generate(passphrase,
                                        site,
                                        localbox_client.authenticator.username)
            data = {'private_key': keys.get_key(fingerprint, True),
                    'public_key': keys.get_key(fingerprint, False)}
            data_json = json.dumps(data)
            # register key data
            result = localbox_client.call_user(data_json)

        if result is not None:
            self._passphrase[site] = passphrase
        return result

    def get_passphrase(self, label, remote=False):
        """
        Get passphrase from memory.

        :param label:
        :param remote: if True and passphrase does not exist, try to via HTTP (localhost)
        :return:
        """
        if remote:
            try:
                # TODO: prop for URL
                passphrase_server_url = 'http://localhost:9090/%s' % label
                passphrase = urllib.urlopen(passphrase_server_url).read()
                getLogger(__name__).debug('got passphrase %s' % passphrase)

                return passphrase
            except urllib.URLError:
                getLogger(__name__).error('Sync client is not running. Failed to get passphrase from client.')

                return None
        else:
            try:
                return self._passphrase[label]
            except KeyError:
                return None

    def store_passphrase(self, passphrase, label, user):
        if gpg().is_passphrase_valid(passphrase=passphrase,
                                     label=label,
                                     user=user):
            self._passphrase[label] = passphrase
        else:
            raise InvalidPassphraseError

    @property
    def logged_in(self):
        return self._logged_in

    @logged_in.setter
    def logged_in(self, value):
        self._logged_in = value


class InvalidPassphraseError(Exception):
    pass
