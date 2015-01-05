try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'LocalBox sync client',
    'author': 'Tjeerd van der Laan',
    'url': 'http://github.com/2EK/Linux-Sync',
    'download_url': 'https://github.com/2EK/Linux-Sync/archive/master.zip',
    'author_email': 'imtal@yolt.nl',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['lox','lox.gui','daemon','iso8601'],
    'scripts': ['lox-client'],
    'name': 'lox-client'
}

setup(**config)
