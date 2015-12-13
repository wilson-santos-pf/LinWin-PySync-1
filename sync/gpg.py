from gnupg import GPG
from StringIO import StringIO

class gpg():
    def __init__(self, folder_path=None, binary_path=None):
        self.gpg = GPG(gpgbinary=binary_path, gnupghome=folder_path)
        # fixstuff with home dir
    def add_key(self, public_key, private_key):
        result1 = self.gpg.import_keys(public_key)
        result2 = self.gpg.import_keys(private_key)
        assert result1
        assert result2
    def encrypt(data, user):
      
