from setuptools import setup, find_packages
from platform import system
from distutils.sysconfig import get_python_lib
from subprocess import check_output

#
# script to register Python 2.0 or later for use with win32all
# and other extensions that require Python registry settings
#
# written by Joakim Low for Secret Labs AB / PythonWare
#
# source:
# http://www.pythonware.com/products/works/articles/regpy20.htm

import sys

try:
   from _winreg import *
except ImportError:
   print "this is not windows"

# tweak as necessary
version = sys.version[:3]
installpath = sys.prefix

regpath = "SOFTWARE\\Python\\Pythoncore\\%s\\" % (version)
installkey = "InstallPath"
pythonkey = "PythonPath"
pythonpath = "%s;%s\\Lib\\;%s\\DLLs\\" % (
    installpath, installpath, installpath
)

def RegisterPy():
    try:
        reg = OpenKey(HKEY_LOCAL_MACHINE, regpath)
    except EnvironmentError:
        try:
            reg = CreateKey(HKEY_LOCAL_MACHINE, regpath)
            SetValue(reg, installkey, REG_SZ, installpath)
            SetValue(reg, pythonkey, REG_SZ, pythonpath)
            CloseKey(reg)
        except:
            print "*** Unable to register!"
            return
        print "--- Python", version, "is now registered!"
        return
    if (QueryValue(reg, installkey) == installpath and
        QueryValue(reg, pythonkey) == pythonpath):
        CloseKey(reg)
        print "=== Python", version, "is already registered!"
        return
    CloseKey(reg)
    print "*** Unable to register!"
    print "*** You probably have another Python installation!"

try:
 RegisterPy()
except NameError:
   print "this is not windows"

data_files = [
    ('localbox', ['localbox.ico'])
]

if system() == 'Windows' or system().startswith('CYGWIN'):
    data_files += [('gpg', ['libs/iconv.dll', 'libs/gpg.exe'])]

try:
    git_number = len([elem for elem in check_output(
        ['git', 'log']).split("\n") if elem.startswith('commit ')])
    if git_number != 0:
        versionno = "0.1a" + str(git_number)
except WindowsError:
    print "Sorry; git executable needed for a version number"
    versionno = "0.1a.nogit"


setup(
    name="LocalBoxSync",
    version=versionno,
    packages=find_packages(),
    py_modules=['gnupg'],
    author="Letshare Holding B.V.",
    author_email="ivo@libbit.eu",
    description="",
    license="all rights reserved",
    url="http://box.yourlocalbox.org",
    data_files=data_files,
    package_data={'sync': ['resources/images/*.png']},
    install_requires = [
        'pkg_resources'
    ]
)
