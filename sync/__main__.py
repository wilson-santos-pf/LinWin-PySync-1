"""
main module for localbox sync
"""
from threading import Lock
from getpass import getpass
from logging import getLogger
from logging import StreamHandler
from threading import Thread
from os.path import join
from os.path import expandvars
from .defaults import KEEP_RUNNING
from .defaults import SITESINI_PATH
from .defaults import SYNCINI_PATH

from .auth import Authenticator
from .auth import AuthenticationError
from .localbox import LocalBox
from .syncer import Syncer
from time import sleep
from .taskbar import taskbarmain
try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError
    from ConfigParser import NoSectionError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401,W0611
    # pylint: disable=F0401
    from configparser import NoOptionError
    from configparser import NoSectionError
    raw_input = input #pylint: disable=W0622,C0103

class SyncRunner(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None,
                 verbose=None, syncer=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args,
                        kwargs=kwargs, verbose=verbose)
        self.setDaemon(True)
        self.syncer = syncer
        self.lock = Lock()

    def run(self):
        self.lock.acquire()
        # TODO: Direction
        self.syncer.syncsync()
        self.lock.release()


def stop_running():
    global KEEP_RUNNING
    KEEP_RUNNING = False

def main():
    """
    temp test function
    """
    handler = StreamHandler()
    fhandler = FileHandler('localbox-sync.log')
    for name in 'main', 'database', 'auth', 'localbox':
        logger = getLogger(name)
        logger.addHandler(handler)
        logger.addHandler(fhandler)
        logger.setLevel(5)
    location = SITESINI_PATH
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
                print("Don't have client credentials for this host yet."
                      " We need to log in with your data for once.")
                username = raw_input("Username: ")
                password = getpass("Password: ")
                try:
                    authenticator.init_authenticate(username, password)
                except AuthenticationError:
                    print("authentication data incorrect. Skipping entry.")
            else:
                syncer = Syncer(localbox, path, direction)
                sites.append(syncer)
        except NoOptionError as error:
            string = "Skipping '%s' due to missing option '%s'" % (section, error.option)
            getLogger('main').debug(string)
    configparser.read(SYNCINI_PATH)
    try:
        delay = int(configparser.get('sync', 'delay'))
    except (NoSectionError, NoOptionError):
        delay = 3600
    while KEEP_RUNNING:
        for syncer in sites:
            #runner = SyncRunner(syncer=syncer)
            if syncer.direction == 'up':
                syncer.upsync()
            if syncer.direction == 'down':
                syncer.downsync()
            if syncer.direction == 'sync':
                syncer.syncsync()
        sleep(delay)

if __name__ == '__main__':
    MAIN = Thread(target=main)
    MAIN.daemon = True
    taskbarmain()
