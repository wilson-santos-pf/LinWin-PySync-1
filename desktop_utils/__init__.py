import logging
from ConfigParser import SafeConfigParser

from sync.defaults import SYNCINI_PATH
from desktop_utils.defaults import LOG_PATH
from loxcommon.log import prepare_logging

configparser = SafeConfigParser()
configparser.read(SYNCINI_PATH)

if not configparser.has_section('logging'):
    configparser.add_section('logging')
    configparser.set('logging', 'console', 'False')

prepare_logging(configparser, log_path=LOG_PATH)
logging.getLogger('gnupg').setLevel(logging.ERROR)