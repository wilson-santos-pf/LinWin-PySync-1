"""
main module for localbox sync
"""
from getpass import getpass
from logging import getLogger
from logging import StreamHandler

from .auth import Authenticator
from .auth import AuthenticationError
from .localbox import LocalBox
from .syncer import Syncer
try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401,W0611
    # pylint: disable=F0401
    from configparser import NoOptionError
    raw_input = input #pylint: disable=W0622

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

    print "LocalBox:"
    syncer.localbox_metadata.debug_print()
    print "FilePath:"
    syncer.filepath_metadata.debug_print()
    print "downsync:"
    syncer.downsync()
    print "upsync:"
    syncer.upsync()

if __name__ == '__main__':
    main()
