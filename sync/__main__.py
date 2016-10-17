"""
main module for localbox sync
"""
from getpass import getpass
from logging import getLogger
from os import makedirs
from os.path import dirname
from os.path import isdir
from threading import Event
from threading import Thread

from sync.controllers.localbox_ctrl import SyncsController
from sync.gui.taskbar import taskbarmain
from .auth import AuthenticationError
from .defaults import LOG_PATH
from .defaults import SITESINI_PATH
from .defaults import SYNCINI_PATH
from .defaults import VERSION
from .localbox import LocalBox
from .syncer import Syncer, SyncRunner

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

KEEP_RUNNING = True

def stop_running():
    """
    Tell the syncers that it is time to quit by setting a global variable
    """
    global KEEP_RUNNING
    KEEP_RUNNING = False


def get_syncers():
    """
    returns a list of Syncers. One per configured localbox instance.
    """
    syncs_ctrl = SyncsController()

    sites = []
    for sync_item in syncs_ctrl:
        getLogger(__name__).info("Syncing %s", sync_item.label)
        try:
            url = sync_item.url
            path = sync_item.path
            direction = sync_item.direction
            label = sync_item.label
            localbox_client = LocalBox(url, label)
            if not localbox_client.authenticator.has_client_credentials():
                getLogger(__name__).info("Don't have client credentials for "
                                         "this host yet. We need to log in with"
                                         " your data for once.")
                username = raw_input("Username: ")
                password = getpass("Password: ")
                try:
                    localbox_client.authenticator.init_authenticate(username, password)
                except AuthenticationError as error:
                    getLogger(__name__).exception(error)
                    getLogger(__name__).info("authentication data incorrect. "
                                             "Skipping entry.")
            else:
                syncer = Syncer(localbox_client, path, direction, name=sync_item.label)
                sites.append(syncer)
        except NoOptionError as error:
            getLogger(__name__).exception(error)
            string = "Skipping '%s' due to missing option '%s'" % \
                     (sync_item, error.option)
            getLogger(__name__).info(string)
        except URLError as error:
            getLogger(__name__).exception(error)
            string = "Skipping '%s' because it cannot be reached" % \
                     (sync_item)
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
            threadpool = []
            for syncer in get_syncers():
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
    getLogger(__name__).info("LocalBox Sync Version: %s", VERSION)
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
