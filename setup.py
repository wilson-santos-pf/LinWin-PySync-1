try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'LocalBox sync client',
    'author': 'Tjeerd van der Laan',
    'url': 'http://github.com/imtal/lox-client',
    'download_url': 'Where to download it.',
    'author_email': 'imtal@yolt.nl',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['lox','daemon','iso8601'],
    'scripts': ['lox-client'],
    'name': 'lox-client'
}

setup(**config)
