from .database import database_execute
from logging import getLogger
from gnupg import GPG
from os.path import join
from os.path import isfile
from base64 import b64encode
from base64 import b64decode
try:
    from ConfigParser import ConfigParser  # pylint: disable=F0401
    from StringIO import StringIO  # pylint: disable=F0401
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401
    from io import StringIO

from distutils.sysconfig import project_base
from .defaults import SITESINI_PATH


class gpg(object):

    """
    module to wrap the gnupg library and gpg binary
    """

    def __init__(self, folder_path=None, binary_path=None):
        # ugly but working
        if binary_path is None:
            binary_path = join(project_base, "gpg", "gpg.exe")
            if not isfile(binary_path):
                binary_path = join(project_base, 'gpg')
                if not isfile(binary_path):
                    binary_path = None
        self.gpg = GPG(gpgbinary=binary_path, gnupghome=folder_path,
                       verbose=False, options="--allow-non-selfsigned-uid")

    # def remove_passphrase(self, fingerprint):
    # def add_passphrase(self, fingerprint, passphrase):

    def get_key(self, fingerprint, private):
        key = self.gpg.export_keys(fingerprint, private, armor=False)
        return b64encode(key.encode('ISO8859-1'))

    def add_pubkey(self, public_key, site, user):
        """
        add a public key to the key database
        """
        result = self.gpg.import_keys(public_key)
        fingerprint = result.fingerprints[0]
        sql = "INSERT INTO keys (site, user, fingerprint) VALUES (?, ?, ?);"
        database_execute(sql, (site, user, fingerprint))
        return fingerprint

    def add_keypair(self, public_key, private_key, site, user, passphrase):
        """
        add a keypair into the gpg key database
        """
        print(public_key)
        print(private_key)
        print(site)
        print(user)
        print(passphrase)
        try:
            result1 = self.gpg.import_keys(b64decode(public_key))
            result2 = self.gpg.import_keys(b64decode(private_key))
        except TypeError as error:
            print(error)
            print(public_key)
            print(private_key)
        # make sure this is a key _pair_
        try:
            assert result1.fingerprints[0] == result2.fingerprints[0]
        except (IndexError, AssertionError) as error:
            getLogger('error').exception(error)
            getLogger('gpg').debug(str(result1.fingerprints))
            getLogger('gpg').debug(str(result2.fingerprints))
            return None
        fingerprint = result1.fingerprints[0]
        sign = self.gpg.sign("test", keyid=fingerprint, passphrase=passphrase)
        if sign.data == '':  # pylint: disable=E1101
            return None
        else:
            sql = "INSERT INTO keys (site, user, fingerprint) VALUES (?, ?, ?)"
            database_execute(sql, (site, user, fingerprint))
            return fingerprint

    def generate(self, passphrase, site, user):
        data = self.gpg.gen_key_input(key_length=2048, passphrase=passphrase)
        dat = self.gpg.gen_key(data)
        fingerprint = dat.fingerprint
        sql = "INSERT INTO keys (site, user, fingerprint) VALUES (?, ?, ?);"
        database_execute(sql, (site, user, fingerprint))
        return fingerprint

    def has_key(self, site, user):
        sql = "select fingerprint from keys where site = ? and user = ?"
        result = database_execute(sql, (site, user))
        if result == []:
            return False
        return True

    def encrypt(self, data, site, user, armor=False):
        """
        encrypt data for user at site.
        """
        sql = "select fingerprint from keys where site = ? and user = ?"
        result = database_execute(sql, (site, user))
        fingerprint = result[0][0]
        cryptdata = self.gpg.encrypt_file(StringIO(data), fingerprint,
                                          always_trust=True, armor=armor)
        return str(cryptdata)

    def decrypt(self, data, site):
        """
        decrypt data received from site.
        """
        configparser = ConfigParser()
        configparser.read(SITESINI_PATH)
        passphrase = configparser.get(site, 'passphrase')
        datafile= StringIO(data)
        outfile = StringIO()
        result = self.gpg.decrypt_file(datafile, passphrase=passphrase, always_trust=True)
        return str(result)
