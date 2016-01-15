"""
listing of values/variables' default values.
"""
from os.path import exists
from os.path import join
from os.path import expandvars
from distutils.sysconfig import project_base
from os.path import abspath
from os.path import dirname

KEEP_RUNNING = True

PACKAGEDIR = dirname(abspath(__file__))

if exists("c:"):
    APPDIR = join(expandvars("%APPDATA%"), 'LocalBox')
else:
    # We assume anything nonwindows is POSIX-like enough
    APPDIR = join(expandvars("$HOME"), '.config', 'localbox')

SYNCINI_PATH = join(APPDIR, 'sync.ini')
SITESINI_PATH = join(APPDIR, 'sites.ini')
DATABASE_PATH = join(APPDIR, 'database.sqlite3')
LOG_PATH = join(APPDIR, 'localbox-sync.log')
LOCALE_PATH = join(PACKAGEDIR, 'locale')
