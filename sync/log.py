"""
main module for localbox sync
"""
from logging import getLogger
from logging import StreamHandler
from logging import FileHandler
from logging import Formatter
from .defaults import SYNCINI_PATH
from .defaults import LOG_PATH
from sys import stdout

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


def prepare_logging():
    """
    sets up the root logger, Stream/File handlers, log format and log level
    """
    location = SYNCINI_PATH
    configparser = ConfigParser()
    configparser.read(location)

    handlers = [StreamHandler(stdout), FileHandler(LOG_PATH)]
    log_text_format = Formatter(
        "%(asctime)s - %(module)s %(lineno)s - %(threadName)s - %(levelname)s - %(message)s")
    logger = getLogger()  # Root logger
    for handler in handlers:
        handler.setFormatter(log_text_format)
        logger.addHandler(handler)
        logger.setLevel(0)
        logger.info("Starting LocalBox Sync logger ")
    getLogger('gnupg').setLevel('INFO')
    try:
        for (name, value) in configparser.items('loglevels'):
            getLogger(__name__).info("Setting logger %s to %s", name, value)
            logger = getLogger(name)
            try:
                value = int(value)
            except ValueError:
                if value not in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']:
                    getLogger(__name__).info("unrecognised loglevel %s for logger %s, skipping", value, name)
                    continue
            logger.setLevel(value)
    except NoSectionError:
        pass
