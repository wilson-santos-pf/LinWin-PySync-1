"""
listing of values/variables' default values.
"""
from os.path import exists
from os.path import join
from os.path import expandvars
from os.path import abspath
from os.path import dirname

try:
    from sync.version import VERSION
except ImportError:
    VERSION = open('VERSION').readline().strip()

from subprocess import check_output
GIT_VERSION = check_output(['git','log']).split('\n')[0].split(' ')[1]

KEEP_RUNNING = True

PACKAGEDIR = dirname(abspath(__file__))

# assuming 'c:' only exists on 'Windows' machines and adjust path accordingly
if exists("c:"):
    APPDIR = join(expandvars("%APPDATA%"), 'LocalBox')
else:
    # We assume anything nonwindows is POSIX-like
    APPDIR = join(expandvars("$HOME"), '.config', 'localbox')

SYNCINI_PATH = join(APPDIR, 'sync.ini')
SITESINI_PATH = join(APPDIR, 'sites.ini')
LOCALBOX_SITES_PATH = join(APPDIR, 'sites.pickle')
LOCALBOX_PREFERENCES_PATH = join(APPDIR, 'prefs.pickle')
LOCALBOX_ACCOUNT_PATH = join(APPDIR, 'account.pickle')
DATABASE_PATH = join(APPDIR, 'database.sqlite3')
LOG_PATH = join(APPDIR, 'localbox-sync.log')
LOCALE_PATH = join(PACKAGEDIR, 'locale')
DEFAULT_LANGUAGE = 'ENGLISH'

OLD_SYNC_STATUS = join(APPDIR, 'localbox.pickle.')
