"""
main module for localbox sync
"""
from pprint import pprint
from getpass import getpass
from logging import getLogger
from logging import StreamHandler

from .auth import Authenticator
from .auth import AuthenticationError
from .localbox import LocalBoxSync
try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError, NoSectionError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401
    # pylint: disable=F0401
    from configparser import NoOptionError, NoSectionError
    raw_input = input

def main():
    """
    temp test function
    """
    handler = StreamHandler()
    for name in 'main', 'database', 'auth', 'localbox':
        logger = getLogger(name)
        logger.addHandler(StreamHandler())
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
            sites.append(LocalBoxSync(url, path, direction))
        except NoOptionError as error:
            getLogger('main').debug("Skipping LocalBox '%s' due to missing option '%s'" % (section, error.option))
    for site in sites:
        x = Authenticator(site.get_authentication_url(), site.url)
        if not x.has_client_credentials():
            print("Don't have client credentials for this host yet. We need to log in with your data for once.")
            username = raw_input("Username: ")
            password = getpass("Password: ")
            try:
                result = x.init_authenticate(username, password)
            except AuthenticationError:
                print("authentication data incorrect. Skipping entry for now")
    exit(1)
    

    ConfigSingleton('sync.ini')
    auth = Authenticator('http://localhost:8000/', "http://localhost:8001")
    #auth.init_authenticate('user', 'pass')
    #auth.client_id = 'id608516886'
    #auth.client_secret = 'secret389242875'
    if auth.has_client_credentials():
        getLogger('main').debug("Already have client credentials, using those")
        auth.authenticate()
    else:
        getLogger('main').debug("Don't have client credentials yet, using Resource Owner Credentials")
        auth.init_authenticate('user', 'pass')
       
    print(auth.get_authorization_header())

if __name__ == '__main__':
    main()
