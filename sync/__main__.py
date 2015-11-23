"""
main module for localbox sync
"""

from .auth import Authenticator
from .database import ConfigSingleton

def main():
    """
    temp test function
    """
    ConfigSingleton('sync.ini')
    auth = Authenticator('http://localhost:8000/', "localbox_url2")
    auth.init_authenticate('user', 'pass')
    #auth.client_id = 'id608516886'
    #auth.client_secret = 'secret389242875'
    auth.authenticate()
    print auth.get_authorization_header()

if __name__ == '__main__':
    main()
