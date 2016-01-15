"""
listing of values/variables' default values.
"""
from os.path import exists
from os.path import join
from os.path import expandvars

KEEP_RUNNING = True

if exists("c:"):
    APPDIR = join(expandvars("%APPDATA%"), 'LocalBox')
    TRANSLATEDIR=join(expandvars("%APPDATA%"), 'LocalBox', 'locale')
else:
    # We assume anything nonwindows is POSIX-like enough
    APPDIR = join(expandvars("$HOME"), '.config', 'localbox')
    TRANSLATEDIR=join(expandvars("$HOME"), '.config', 'localbox', 'locale')

SYNCINI_PATH = join(APPDIR, 'sync.ini')
SITESINI_PATH = join(APPDIR, 'sites.ini')
DATABASE_PATH = join(APPDIR, 'database.sqlite3')
LOG_PATH = join(APPDIR, 'localbox-sync.log')
