from ConfigParser import SafeConfigParser

from sync.defaults import SYNCINI_PATH, LOG_PATH
from loxcommon.log import prepare_logging

configparser = SafeConfigParser()
configparser.read(SYNCINI_PATH)

if not configparser.has_section('logging'):
    configparser.add_section('logging')
    configparser.set('logging', 'console', 'True')

prepare_logging(configparser, log_path=LOG_PATH)
