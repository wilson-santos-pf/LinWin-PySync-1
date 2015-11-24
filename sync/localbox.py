"""
localbox client library
"""
try:
    from urllib2 import urlopen
    from urllib2 import HTTPError
except ImportError:
    from urllib.request import urlopen # pylint: disable=F0401,E0611
    from urllib.error import HTTPError # pylint: disable=F0401,E0611


class AlreadyAuthenticatedError(Exception):
    pass

class LocalBoxSync(object):
    def __init__(self, url, path, direction):
        self.url = url
        self.path = path
        if direction not in ['up', 'down', 'sync']:
            raise ValueError("The direction must be either 'up', 'down' or 'sync'")
        self.direction = direction
        self.authentication_url = None

    def get_authentication_url(self):
        if self.authentication_url != None:
            return authentication_url
        else:
            try:
                urlopen(self.url)
            except HTTPError as error:
                auth_header = error.headers['WWW-Authenticate'].split(' ')
                bearer = False
                for field in auth_header:
                    if bearer:
                        try:
                            entry = field.split('=', 1)
                            if entry[0].lower() == "domain":
                                return entry[1][1:-1]
                        except ValueError as e:
                            bearer = False
                    if field.lower() == 'bearer':
                        bearer = True
        raise AlreadyAuthenticatedError()


