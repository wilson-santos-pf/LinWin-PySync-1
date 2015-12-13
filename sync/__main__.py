"""
main module for localbox sync
"""
from getpass import getpass
from logging import getLogger
from logging import StreamHandler
from threading import Thread
from json import loads

from sys import argv
from .auth import Authenticator
from .auth import AuthenticationError
from .localbox import LocalBox
from .syncer import Syncer
from .gui import main as guimain
from time import sleep
try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401,W0611
    # pylint: disable=F0401
    from configparser import NoOptionError
    raw_input = input #pylint: disable=W0622

class SyncRunner(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, syncer=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs, verbose=verbose)
        self.syncer = syncer

    def run(self):
        syncer.syncsync()
        

def main():
    """
    temp test function
    """
    handler = StreamHandler()
    for name in 'main', 'database', 'auth', 'localbox':
        logger = getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(5)
    location='sites.ini'
    configparser = ConfigParser()
    configparser.read(location)
    sites = []
    for section in configparser.sections():
        try:
            url = configparser.get(section, 'url')
            path = configparser.get(section, 'path')
            direction = configparser.get(section, 'direction')
            localbox = LocalBox(url)
            authenticator = Authenticator(localbox.get_authentication_url(), section)
            localbox.add_authenticator(authenticator)
            from pprint import pprint
            pprint(localbox.call_user().__dict__)
            keys = loads(localbox.call_user().read())
            pubkey = keys['public_key']
            privkey = keys['private_key']
            print pubkey
            print privkey
            
            from Crypto.PublicKey import RSA
            from Crypto.Util import asn1
            from base64 import b64decode
            seq = asn1.DerSequence()
            key2= b64decode(pubkey)
            print key2
            seq.decode(key2)
            key =  RSA.construct( (seq[0], seq[1]) )
            print(key)
            pprint(key)
            print(key.__dict__)
           


            if not authenticator.has_client_credentials():

                print("Don't have client credentials for this host yet. We need to log in with your data for once.")
                username = raw_input("Username: ")
                password = getpass("Password: ")
                try:
                    result = authenticator.init_authenticate(username, password)
                    from pprint import pprint
                    pprint(result)
                    sites.append(localbox)
                except AuthenticationError:
                    print("authentication data incorrect. Skipping entry.")
            else:
                syncer = Syncer(localbox, path, direction)
                sites.append(syncer)
        except NoOptionError as error:
            string = "Skipping LocalBox '%s' due to missing option '%s'" % (section, error.option)
            getLogger('main').debug(string)
    configparser.read('sync.ini')
    delay = int(configparser.get('sync','delay'))
    while(True):
        for syncer in sites:
            runner = SyncRunner(syncer=syncer)
            if syncer.direction == 'up':
                syncer.syncup()
            if syncer.direction == 'down':
                syncer.syncdown()
            if syncer.direction == 'sync':
                syncer.syncsync()
        sleep(delay)

if __name__ == '__main__':
    print argv
    if argv[-1] == "--gui":
        guimain()
    else:
        main()
