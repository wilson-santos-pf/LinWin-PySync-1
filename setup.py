try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
#from distutils.core import setup
from distutils import cmd
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build
from distutils.core import setup
from babel.messages import frontend as babel

import shutil
import site
from pprint import pprint
import subprocess
import os

NAME = 'lox-client'
PACKAGES = ['lox','lox.gui']
DESCRIPTION = 'LocalBox sync client',
AUTHOR = 'Tjeerd van der Laan',
AUTHOR_EMAIL = 'imtal@yolt.nl',
VERSION = '0.2'

DATA_FILES = [
        ('/usr/share/locale/nl/LC_MESSAGES',["build/locale/nl/LC_MESSAGES/lox-client.mo"]),
        ('/usr/share/locale/fy/LC_MESSAGES',["build/locale/fy/LC_MESSAGES/lox-client.mo"]),
        ('/usr/share/applications',["lox-client.desktop"]),
        ('/usr/share/icons',["lox/gui/localbox_256.png"])
    ]

setup(
    description = DESCRIPTION,
    author = AUTHOR,
    url = 'http://github.com/2EK/Linux-Sync',
    download_url = 'https://github.com/2EK/Linux-Sync/archive/master.zip',
    author_email = AUTHOR_EMAIL,
    version = VERSION,
    packages = PACKAGES,
    data_files = DATA_FILES,
    package_data = {
        'lox.gui': ['*.png']
    },
    scripts = ['lox-client'],
    #cmdclass = {
    #    'compile_catalog': babel.compile_catalog,
    #    'extract_messages': babel.extract_messages,
    #    'init_catalog': babel.init_catalog,
    #    'update_catalog': babel.update_catalog,
    #},
    name = NAME
)

