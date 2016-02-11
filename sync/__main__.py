"""
main module for localbox sync
"""
from threading import Lock
from getpass import getpass
from logging import getLogger
from logging import StreamHandler
from logging import FileHandler
from threading import Thread
from threading import Event
from os import makedirs
from os.path import isdir
from os.path import dirname
from .defaults import KEEP_RUNNING
from .defaults import SITESINI_PATH
from .defaults import SYNCINI_PATH
from .defaults import LOG_PATH
from sys import stdout

from .auth import Authenticator
from .auth import AuthenticationError
from .localbox import LocalBox
from .syncer import Syncer
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
    raw_input = input  # pylint: disable=W0622,C0103


class SyncRunner(Thread):

    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None, verbose=None, syncer=None):
        Thread.__init__(self, group=group, target=target, name=name,
                        args=args, kwargs=kwargs, verbose=verbose)
        self.setDaemon(True)
        self.syncer = syncer
        self.lock = Lock()
        getLogger('main').info("SyncRunner started")

    def run(self):
        getLogger('main').info("SyncRunner " + self.name + " started")
        self.lock.acquire()
        # TODO: Direction
        self.syncer.syncsync()
        self.lock.release()
        getLogger('main').info("SyncRunner " + self.name + " finished")


def stop_running():
    global KEEP_RUNNING
    KEEP_RUNNING = False


def get_site_list():
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
            authenticator = Authenticator(localbox.get_authentication_url(),
                                          section)
            localbox.add_authenticator(authenticator)
            if not authenticator.has_client_credentials():
                getLogger('main').info("Don't have client credentials for "
                                       "this host yet. We need to log in with"
                                       " your data for once.")
                username = raw_input("Username: ")
                password = getpass("Password: ")
                try:
                    authenticator.init_authenticate(username, password)
                except AuthenticationError as error:
                    getLogger('error').exception(error)
                    getLogger('main').info("authentication data incorrect. "
                                           "Skipping entry.")
            else:
                syncer = Syncer(localbox, path, direction)
                sites.append(syncer)
        except NoOptionError as error:
            getLogger('error').exception(error)
            string = "Skipping '%s' due to missing option '%s'" % \
                     (section, error.option)
            getLogger('main').info(string)
    return sites


def main(waitevent=None):
    """
    temp test function
    """
    sites = get_site_list()
    location = SITESINI_PATH
    configparser = ConfigParser()
    configparser.read(location)
    try:
        configparser.read(SYNCINI_PATH)
        try:
            delay = int(configparser.get('sync', 'delay'))
        except (NoSectionError, NoOptionError) as error:
            getLogger('error').exception(error)
            delay = 3600
        while KEEP_RUNNING:
            getLogger('localbox').debug("starting loop")
            for syncer in sites:
                runner = SyncRunner(syncer=syncer)
                runner.start()
                # if syncer.direction == 'up':
                #     syncer.upsync()
                # if syncer.direction == 'down':
                #     syncer.downsync()
                # if syncer.direction == 'sync':
                #     syncer.syncsync()
            getLogger('localbox').debug("waiting")
            if waitevent.wait(delay):
                getLogger('localbox').debug("stopped waiting")
                waitevent.clear()
            else:
                getLogger('localbox').debug("done waiting")
    except Exception as error:  # pylint: disable=W0703
        getLogger('error').exception(error)


if __name__ == '__main__':
    try:
        if not isdir(dirname(LOG_PATH)):
            makedirs(dirname(LOG_PATH))
        handlers = [StreamHandler(stdout), FileHandler(LOG_PATH)]
        for name in 'main', 'database', 'auth', 'localbox', 'wizard', 'error', \
                'gpg', 'taskbar', 'gui':
            logger = getLogger(name)
            for handler in handlers:
                logger.addHandler(handler)
            logger.setLevel(5)
            logger.info("Starting Localbox Sync logger " + name)

        EVENT = Event()
        EVENT.clear()
        MAIN = Thread(target=main, args=[EVENT])
        MAIN.daemon = True
        MAIN.start()

        taskbarmain(EVENT)
    except Exception as error:  # pylint: disable=W0703
        getLogger('error').exception(error)
