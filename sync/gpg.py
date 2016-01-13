from .database import database_execute
from ConfigParser import ConfigParser
from gnupg import GPG
from StringIO import StringIO
from os.path import join
from os.path import isfile
from os.path import expandvars

from distutils.sysconfig import project_base

class gpg(object):
    """
    module to wrap the gnupg library and gpg binary
    """
    def __init__(self, folder_path=None, binary_path=None):
        #ugly but working
        if binary_path is None:
            binary_path = join(project_base, "gpg", "gpg.exe")
            if not isfile(binary_path):
                binary_path = join(project_base, 'gpg')
                if not isfile(binary_path):
                    binary_path = None
        self.gpg = GPG(gpgbinary=binary_path, gnupghome=folder_path,
                       verbose=False, options="--allow-non-selfsigned-uid")

    #def remove_passphrase(self, fingerprint):

    #def add_passphrase(self, fingerprint, passphrase):

    def add_pubkey(self, public_key, site, user):
        """
        add a public key to the key database
        """
        result = self.gpg.import_keys(public_key)
        fingerprint = result.fingerprints[0]
        sql = "INSERT INTO keys (site, user, fingerprint) VALUES (?, ?, ?);"
        database_execute(sql, (site, user, fingerprint))
        return fingerprint


    def add_keypair(self, public_key, private_key, site, user):
        """
        add a keypair into the gpg key database
        """
        result1 = self.gpg.import_keys(public_key)
        result2 = self.gpg.import_keys(private_key)
        # make sure this is a key _pair_
        assert result1.fingerprints[0] == result2.fingerprints[0]
        fingerprint = result1.fingerprints[0]
        sql = "INSERT INTO keys (site, user, fingerprint) VALUES (?, ?, ?);"
        database_execute(sql, (site, user, fingerprint))
        return fingerprint

    def encrypt(self, data, site, user):
        """
        encrypt data for user at site.
        """
        sql = "select fingerprint from keys where site = ? and user = ?"
        result = database_execute(sql, (site, user))
        fingerprint = result[0][0]
        print fingerprint
        cryptdata = self.gpg.encrypt_file(StringIO(data), fingerprint,
                                          always_trust=True, armor=False)
        return cryptdata

    def decrypt(self, data, site):
        """
        decrypt data received from site.
        """
        configparser = ConfigParser()
        configparser.read(join(expandvars("%APPDATA%"), 'LocalBox', 'sites.ini'))
        passphrase = configparser.get(site, 'passphrase')
        return str(self.gpg.decrypt_file(StringIO(data), passphrase=passphrase))

