import json
from logging import getLogger

from sync.gpg import gpg


class LoginController(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LoginController, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._logged_in = False
        self._username = None
        self._passphrase = dict()
        self._keys = dict()

    def store_keys(self, localbox_client, pubkey, privkey, passphrase):
        username = localbox_client.authenticator.username
        label = localbox_client.authenticator.label
        # set up gpg
        keys = gpg()
        if pubkey is not None and privkey is not None:
            getLogger(__name__).debug("private key found and public key found")

            result = keys.add_keypair(pubkey,
                                      privkey,
                                      label,
                                      username,
                                      passphrase)
            if result is None:
                getLogger(__name__).debug("could not add keypair")
        else:
            getLogger(__name__).debug("public keys not found. generating...")
            fingerprint = keys.generate(passphrase,
                                        label,
                                        localbox_client.authenticator.username)
            data = {'private_key': keys.get_key(fingerprint, True),
                    'public_key': keys.get_key(fingerprint, False)}
            data_json = json.dumps(data)
            # register key data
            result = localbox_client.call_user(data_json)

        self._username = username
        self._passphrase[label] = passphrase
        return result

    def get_passphrase(self, label):
        try:
            return self._passphrase[label]
        except KeyError:
            return None

    def is_passphrase_valid(self, passphrase, label, user):
        if gpg().is_passphrase_valid(passphrase=passphrase,
                                     label=label,
                                     user=user):
            self._passphrase[label] = passphrase
            return True
        return False

    @property
    def logged_in(self):
        return self._logged_in

    @logged_in.setter
    def logged_in(self, value):
        self._logged_in = value
