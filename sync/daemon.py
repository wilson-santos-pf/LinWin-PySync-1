from ConfigParser import ConfigParser
from ConfigParser import NoOptionError
from .database import database_execute
from .localbox import LocalBox
from .auth import Authenticator
from .auth import AuthenticationError
from os.path import isdir

from threading import Event

def main():
    location='sync.ini'
    configparser = ConfigParser()
    configparser.read(location)

if __name__ == "__main__":
    main()
