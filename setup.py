from setuptools import setup, find_packages
from platform import system
from distutils.sysconfig import get_python_lib
from subprocess import check_output

data_files = [('localbox', ['localbox.ico'])]

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
    data_files=data_files
)
