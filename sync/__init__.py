import logging, signal
from ConfigParser import SafeConfigParser

from sync.defaults import SYNCINI_PATH, LOG_PATH
from loxcommon.log import prepare_logging

configparser = SafeConfigParser()
configparser.read(SYNCINI_PATH)

if not configparser.has_section('logging'):
    configparser.add_section('logging')
    configparser.set('logging', 'console', 'True')

prepare_logging(configparser, log_path=LOG_PATH)
logging.getLogger('gnupg').setLevel(logging.ERROR)


def remove_decrypted_files(signum=None, frame=None):
    import os, desktop_utils.controllers.openfiles_ctrl as ctrl

    logging.getLogger(__name__).info('removing decrypted files')
    for filename in ctrl.load():
        try:
            os.remove(filename)
        except Exception as ex:
            logging.getLogger(__name__).error('could not remove file %s, %s' % (filename, ex))

    ctrl.save([])


signal.signal(signal.SIGINT, remove_decrypted_files)
signal.signal(signal.SIGTERM, remove_decrypted_files)
try:
    # only on Windows
    signal.signal(signal.CTRL_C_EVENT, remove_decrypted_files)
except:
    pass
