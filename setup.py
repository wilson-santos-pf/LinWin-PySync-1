from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib


setup(
    name = "Localbox Sync",
    version = "0.1a0",
    packages = find_packages(),
    scripts=['postinstall.py'],
    py_modules = ['gnupg'],
    author = "Letshare Holding B.V.",
    author_email = "ivo@libbit.eu",
    description = "",
    license =  "all rights reserved",
    url = "http://box.yourlocalbox.org",
    #packages = 'gnupg',
    data_files = [('gpg', ['libs/iconv.dll', 'libs/gpg.exe']), ('localbox', ['localbox.ico'])]
)
