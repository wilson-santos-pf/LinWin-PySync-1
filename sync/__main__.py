"""
main module for localbox sync
"""
from threading import Lock
from getpass import getpass
from logging import getLogger
from logging import StreamHandler
from logging import FileHandler
from logging import Formatter
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
from log import prepare_logging

try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError
    from ConfigParser import NoSectionError
    from urllib2 import URLError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401,W0611
    from configparser import NoOptionError  # pylint: disable=F0401,W0611
    from configparser import NoSectionError  # pylint: disable=F0401,W0611
    from urllib.error import URLError  # pylint: disable=F0401,W0611,E0611

    raw_input = input  # pylint: disable=W0622,C0103


class SyncRunner(Thread):
    """
    Thread responsible for synchronizing between the client and one server.
    """

    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None, verbose=None, syncer=None):
        Thread.__init__(self, group=group, target=target, name=name,
                        args=args, kwargs=kwargs, verbose=verbose)
        self.setDaemon(True)
        self.syncer = syncer
        self.lock = Lock()
        getLogger(__name__).info("SyncRunner started")

    def run(self):
        """
        Function that runs one iteration of the synhronization
        """
        getLogger(__name__).info("SyncRunner " + self.name + " started")
        self.lock.acquire()
        self.syncer.syncsync()
        self.lock.release()
        getLogger(__name__).info("SyncRunner " + self.name + " finished")


def stop_running():
    """
    Tell the syncers that it is time to quit by setting a global variable
    """
    global KEEP_RUNNING
    KEEP_RUNNING = False


def get_site_list():
    """
    returns a list of configured localbox instances.
    """
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
                getLogger(__name__).info("Don't have client credentials for "
                                         "this host yet. We need to log in with"
                                         " your data for once.")
                username = raw_input("Username: ")
                password = getpass("Password: ")
                try:
                    authenticator.init_authenticate(username, password)
                except AuthenticationError as error:
                    getLogger(__name__).exception(error)
                    getLogger(__name__).info("authentication data incorrect. "
                                             "Skipping entry.")
            else:
                syncer = Syncer(localbox, path, direction, name=section)
                sites.append(syncer)
        except NoOptionError as error:
            getLogger(__name__).exception(error)
            string = "Skipping '%s' due to missing option '%s'" % \
                     (section, error.option)
            getLogger(__name__).info(string)
        except URLError as error:
            getLogger(__name__).exception(error)
            string = "Skipping '%s' because it cannot be reached" % \
                     (section)
            getLogger(__name__).info(string)

    return sites


def main(waitevent=None):
    """
    temp test function
    """
    location = SITESINI_PATH
    configparser = ConfigParser()
    configparser.read(location)
    try:
        configparser.read(SYNCINI_PATH)
        try:
            delay = int(configparser.get('sync', 'delay'))
        except (NoSectionError, NoOptionError) as error:
            getLogger(__name__).warning("%s in '%s'",
                                        error.message, SYNCINI_PATH)
            delay = 3600
        while KEEP_RUNNING:
            getLogger(__name__).debug("starting loop")
            waitevent.set()
            threadpool=[]
            for syncer in get_site_list():
                runner = SyncRunner(syncer=syncer)
                getLogger(__name__).debug("starting thread %s", runner.name)
                runner.start()
                threadpool.append(runner)
                getLogger(__name__).debug("started thread %s", runner.name)
            for runner in threadpool:
                getLogger(__name__).debug("joining thread %s", runner.name)
                runner.join()
                getLogger(__name__).debug("joined thread %s", runner.name)
            waitevent.clear()
            getLogger(__name__).debug("Cleared Event")
            if waitevent.wait(delay):
                getLogger(__name__).debug("stopped waiting")
            else:
                getLogger(__name__).debug("done waiting")
    except Exception as error:  # pylint: disable=W0703
        getLogger(__name__).exception(error)


if __name__ == '__main__':
    prepare_logging()
    try:
        if not isdir(dirname(LOG_PATH)):
            makedirs(dirname(LOG_PATH))
        EVENT = Event()
        EVENT.clear()
        MAIN = Thread(target=main, args=[EVENT])
        MAIN.daemon = True
        MAIN.start()

        taskbarmain(EVENT)
    except Exception as error:  # pylint: disable=W0703
        getLogger(__name__).exception(error)
