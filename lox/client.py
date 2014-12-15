'''

Main module

Usage:

    import lox.client
    
    lox.client.main()
    # or lox.client.test() for a test run of the sync

Todo:

    Check if daeon runs as expected
    
'''

import os
import sys
import lox.config
import lox.api
import lox.daemon
import lox.session

from lox.error import LoxError
from lox.daemon import Daemon

__author__ = "imtal@yolt.nl"
__copyright__ = "(C) 2014, see LICENSE file"
__version__ = "0.1"

class Supervisor(lox.daemon.Daemon):
    def run(self):
        for Name in lox.config.sessions():
            t = lox.session.Session(Name)
            t.start()

def test():
    t = lox.session.Session('localhost')
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
    elif Action=='test':
        daemon.run()
    elif Action=='stop':
        try:
            daeamon.stop()
            print "LocalBox client: stopped"
        except Exception as e:
            print "LocalBox client: ", e
    elif Action=='restart':
        try:
            daeamon.restart()
            print "LocalBox client: restarted"
        except Exception as e:
            print "LocalBox client: ", e
    elif Action=='help':
        Cmd = os.path.basename(sys.argv[0])
        print "LocalBox desktop sync version {}".format(__version__)
        print ""
        print "Usage: {} [command]".format(Cmd)
        print ""
        print "       start  - starts the client"
        print "       stop   - stops the client"
        print "       config - edit the configuration file"
        print "       reload - reloads the confguration"
        print "       sync   - force a synchronization"
        print "       status - show the status of the client"
    else:
        Cmd = os.path.basename(sys.argv[0])
        print "Usage: %s start|stop|reload|sync|status|help|... " % Cmd
    print ""
        
if __name__ == '__main__':
    lox.client.main()
