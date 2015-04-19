'''
Module containing helper class for encryption of files

Please note:
(1) The files are AES encrypted
(2) For that reason, the file is aligned (padded) to a block size of 16
(3) The original file length is not stored, so decryption leaves a padded file (!)
(4) The initialization vector is stored with the key (!) and not in the file
(5) The key and initialization vector are PGP encrypted
(6) PGP public and private (!) key are stored on the server
(7) PGP keys are not signed
(8) PGP keys and AES keys are stored base64 on the server, module base64 is used
(9) The ~/.lox directory is used for the keyring

'''

import os
import base64
import md5
from Crypto.Cipher import AES
from Crypto import Random
import gnupg
import lox.config as config

class LoxKey:
    key = None
    iv = None


class LoxCrypto:
    '''
    A different private key is generated for each session
    in order to not mix up session security
    '''

    def __init__(self,name):
        _passphrase = None
        conf_dir = os.environ['HOME']+'/.lox'
        os.chmod(conf_dir,0700)
        _gpg = gnupg.GPG(
                            gnupghome=conf_dir,
                            #keyring='lox-client',
                            #secret_keyring='lox-client',
                            verbose=False,
                            options=['--allow-non-selfsigned-uid']
                        )
        _id = config.settings[name]['username']
        # check if private key exists
        input_data = _gpg.gen_key_input(
                            key_type='RSA',
                            key_length=2048,
                            name_email=self._id,
                            name_comment='Localbox user',
                            name_real='Anonymous'
                        )
        _gpg.gen_key(input_data)

    def set_passphrase(password):
        '''
        Store a passphrase for keyring and export/import
        '''
        _passphrase = md5.new(password).digest()

    def get_passphrase(p):
        '''
        Get a passphrase (use?)
        '''
        return _passphrase

    def set_private(self,key):
        '''
        Import a localbox key in the keyring
        '''
        self._gpg.import_keys(key)

    def get_public(self):
        self._gpg.export_keys(self._id)

    def get_private():
        self._gpg.export_keys(self._id,True)

    def gpg_decrypt(self, string):
        '''
        Base64 decode
        PGP decrypt a string (usually the AES key)
        '''
        ciphertext = base64.b64decode(string)
        plaintext = __gpg.decrypt(ciphertext, self._passphrase)
        return plaintext

    def gpg_encrypt(self, string):
        '''
        PGP encrypt a string (usually the AES key)
        then base64 encode
        '''
        ciphertext = __gpg.encrypt(string, self.__passphrase)
        encoded = base64.b64encode(ciphertext)
        return encoded

    def gpg_list(self):
        '''
        List (private) keys in keyring
        '''
        self._gpg.list_keys(True)

    def aes_new_iv(self):
        '''
        Get a new iv as localbox uses a self generated iv
        '''
        new_iv = Random.new().read(AES.block_size)
        return new_iv

    def aes_pad(self, filename):
        '''
        Pad file a to a 16 byte block length,
        needed for an omission at this moment:
        the original file length is not stored
        '''
        size = os.path.getsize(filename)
        if (size % 16) > 0:
            with open(filename, 'wb') as outfile:
                chunk = ' ' * (16 - (size % 16))
                outfile.write(encryptor.encrypt(chunk))

    def aes_encrypt(self, key, iv, filename_in, filename_out, chunksize=64*1024):
        '''
        Encrypt a file with AES to another file,
        use function to decrypt from original file to temp file
        Note: initialization vector and original size are not stored
        '''
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        with open(filename_in, 'rb') as infile:
            with open(filename_out, 'wb') as outfile:
                #outfile.write(struct.pack('<Q', filesize))
                #outfile.write(iv)
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk += ' ' * (16 - len(chunk) % 16)
                    outfile.write(encryptor.encrypt(chunk))

    def aes_decrypt(self, key, iv, filename_in, filename_out, chunksize=64*1024):
        '''
        Decrypt a file with AES to another file,
        use function to decrypt from temp file to final file
        Note: initialization vector and original size are not stored
        '''
        with open(in_filename, 'rb') as infile:
            #origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            #iv = infile.read(16)
            decryptor = AES.new(key, AES.MODE_CBC, iv)
            with open(filename_out, 'wb') as outfile:
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    outfile.write(decryptor.decrypt(chunk))
                #outfile.truncate(origsize)



