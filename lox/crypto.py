'''
Module containing helper functions for encryption of files

Please note:
(1) The files are AES encrypted
(2) For that reason, the file is aligned (padded) to a block size of 16
(3) The original length is never stored, so decryption leaves a padded file
(4) The key and initialization vector are PGP encrypted
(5) PGP public and private (!) key are stored on the server
(6) PGP keys are not signed
(7) PGP keys and AES keys are stored base64 on the server, module base64 is used
(8) The ~/.lox directory is used for the keyring

'''

import base64
from Crypto.Cipher import AES
from Crypto import Random
import gnupg

__passphrase = "secret"

def set_passphrase(p):
    '''
    Store a passphrase for use
    '''
    global __passphrase
    __passphrase = p

def get_passphrase(p):
    '''
    Store a passphrase for use
    '''
    global __passphrase
    return __passphrase


def gpg_import(key):
    '''
    Import a localbox key in the keyring
    '''
    gpg = gnupg.GPG(gnupghome='keyrings', verbose=False, options=['--allow-non-selfsigned-uid'])
    gpg.import_keys(key)

def gpg_decrypt(string, passphrase):
    '''
    PGP decrypt a string (usually the AES key)
    '''
    ciphertext = base64.b64decode(string)
    plaintext = gpg.decrypt(ciphertext, passphrase)
    return plaintext

def gpg_encrypt(string, passphrase):
    '''
    PGP encrypt a string (usually the AES key)
    '''
    ciphertext = gpg.encrypt(string, passphrase)
    encoded = base64.b64encode(ciphertext)
    return encoded

def get_aes_iv():
    '''
    Get a new iv as localbox uses a self generated iv
    '''
    new_iv = Random.new().read(AES.block_size)
    return new_iv

def pad_file(filename):
    '''
    Pad a to a 16 byte block length,
    needed for an omission at this moment:
    the original file length is not stored
    '''
    size = os.path.getsize(filename)
    if (size % 16) > 0:
        with open(filename, 'wb') as outfile:
            chunk = ' ' * (16 - (size % 16))
            outfile.write(encryptor.encrypt(chunk))

def aes_encrypt(key, iv, filename_in, filename_out, chunksize=64*1024):
    '''
    Encrypt a file with AES to another file,
    use function to decrypt from original file to temp file
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

def aes_decrypt(key, iv, filename_in, filename_out, chunksize=64*1024):
    '''
    Decrypt a file with AES to another file,
    use function to decrypt from temp file to final file
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
                outfile.write(encryptor.decrypt(chunk))

