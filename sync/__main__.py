"""
main module for localbox sync
"""
from logging import getLogger
from os import makedirs
from os.path import dirname
from os.path import isdir
from threading import Event

from sync.gui.taskbar import taskbarmain
from sync.syncer import MainSyncer
from .defaults import LOG_PATH
from .defaults import VERSION

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

if __name__ == '__main__':
    getLogger(__name__).info("LocalBox Sync Version: %s", VERSION)
    try:
        if not isdir(dirname(LOG_PATH)):
            makedirs(dirname(LOG_PATH))
        EVENT = Event()
        EVENT.clear()

        MAIN = MainSyncer(EVENT)
        MAIN.start()

        taskbarmain(MAIN)
    except Exception as error:  # pylint: disable=W0703
        getLogger(__name__).exception(error)
