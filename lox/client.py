'''

Main module

Usage:

    import client
    
    client.main()
    # or client.test() for a test run of the sync

Todo:

    Check if daeon runs as expected
    
'''

import os
import sys
import config
from api import LoxApi
from daemon import Daemon
from session import LoxSession

from error import LoxError
from daemon import Daemon

__author__ = "imtal@yolt.nl"
__copyright__ = "(C) 2014, see LICENSE file"
__version__ = "0.1"

class Supervisor(Daemon):
    def run(self):
        for Name in config.sessions():
            t = LoxSession(Name)
            t.start()

def test():
    t = LoxSession('localhost')
    t.sync()

def main():
    Action = sys.argv[1].lower() if len(sys.argv)>1 else 'undefined'
    pidfile = os.environ['HOME']+'/.lox/lox-client.pid'
    daemon = Supervisor(pidfile)
    print ""
    if Action=='start':
        try:
            daemon.start()
            print "LocalBox client: started"
        except Exception as e:
            print "LocalBox client: ", e
    elif Action=='stop':
        try:
            daemon.stop()
            print "LocalBox client: stopped"
        except Exception as e:
            print "LocalBox client: ", e
    elif Action=='test':
        test()
    elif Action=='restart':
        try:
            daeon.restart()
            print "LocalBox client: restarted"
        except Exception as e:
            print "LocalBox client: ", e
    elif Action=='status':
        s = daemon.status()
        if s is None:
            print "LocalBox client not running ..."
        else:
            print "LocalBox client running with pid %s" % s
    elif Action=='invitations':
        for Name in config.sessions():
            Api = LoxApi(Name)
            Invitations = Api.invitations()
            print "%s: " % Name
            
            for Invite in Invitations:
                Share = Invite[u'share']
                Item = Share[u'item']
                print "  [%s] %s (%s)" % (Invite[u'id'],Item[u'path'],Invite[u'state'])
    elif Action=='help':
        Cmd = os.path.basename(sys.argv[0])
        print "LocalBox desktop sync version {}".format(__version__)
        print ""
        print "Usage: {} [command]".format(Cmd)
        print ""
        print "       start       - starts the client"
        print "       stop        - stops the client"
        print "       test        - run in forground"
        print "       restart     - reloads the confguration"
        print "       invitations - show invitations"
        #print "       sync        - force a synchronization"
        print "       status      - show the status of the client"
        print "       help        - show this help"
    else:
        Cmd = os.path.basename(sys.argv[0])
        print "Usage: %s start|stop|test|invitations|restart|status|help|... " % Cmd
    print ""
        
if __name__ == '__main__':
    main()
