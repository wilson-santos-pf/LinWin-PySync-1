"""
LocalBox synchronization client.
"""
from sync import language
from sync.controllers.preferences_ctrl import PreferencesController

import signal
from ConfigParser import SafeConfigParser
from logging import getLogger, ERROR
from os import mkdir
from os.path import exists

from loxcommon.log import prepare_logging
from sync.defaults import SYNCINI_PATH, LOG_PATH, APPDIR
from ._version import __version__, git_version

if not exists(APPDIR):
    mkdir(APPDIR)

configparser = SafeConfigParser()
configparser.read(SYNCINI_PATH)

if not configparser.has_section('logging'):
    configparser.add_section('logging')
    configparser.set('logging', 'console', 'True')

prepare_logging(configparser, log_path=LOG_PATH)
getLogger('gnupg').setLevel(ERROR)


def remove_decrypted_files(signum=None, frame=None):
    import os, sync.controllers.openfiles_ctrl as ctrl

    getLogger(__name__).info('removing decrypted files')
    for filename in ctrl.load():
        try:
            os.remove(filename)
        except Exception as ex:
            getLogger(__name__).error('could not remove file %s, %s' % (filename, ex))

    ctrl.save([])


signal.signal(signal.SIGINT, remove_decrypted_files)
signal.signal(signal.SIGTERM, remove_decrypted_files)
try:
    # only on Windows
    signal.signal(signal.CTRL_C_EVENT, remove_decrypted_files)
except:
    pass

getLogger(__name__).info("LocalBox Sync Version: %s (%s)", __version__, git_version)

language.set_language(PreferencesController().get_language_abbr())
