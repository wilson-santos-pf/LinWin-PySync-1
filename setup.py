from setuptools import setup, find_packages
from platform import system
from distutils.sysconfig import get_python_lib

data_files = [('localbox', ['localbox.ico'])]

if system() == 'Windows' or system().startswith('CYGWIN'):
    data_files += [('gpg', ['libs/iconv.dll', 'libs/gpg.exe'])]

setup(
    name = "LocalboxSync",
    version = "0.1a002",
    packages = find_packages(),
    py_modules = ['gnupg'],
    author = "Letshare Holding B.V.",
    author_email = "ivo@libbit.eu",
    description = "",
    license =  "all rights reserved",
    url = "http://box.yourlocalbox.org",
    data_files = data_files
)
