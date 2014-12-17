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
import session

from daemon import Daemon

__author__ = "imtal@yolt.nl"
__copyright__ = "(C) 2014, see LICENSE file"
__version__ = "0.1"

class Supervisor(Daemon):
    def run(self):
        for Name in config.sessions():
            t = session.Session(Name)
            t.start()

def test():
    t = session.Session('localhost')
    t.sync()

def main():
    Action = sys.argv[1].lower() if len(sys.argv)>1 else 'undefined'
    pidfile = os.environ['HOME']+'/.client.pid'
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
            daemon.stop()
            print "LocalBox client: stopped"
        except Exception as e:
            print "LocalBox client: ", e
    elif Action=='restart':
        try:
            daemon.restart()
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
        print "       test - run in foreground"
        print "       reload - reloads the confguration"
        print "       sync   - force a synchronization"
        print "       status - show the status of the client"
    else:
        Cmd = os.path.basename(sys.argv[0])
        print "Usage: %s start|stop|reload|sync|status|help|... " % Cmd
    print ""
        
if __name__ == '__main__':
    main()
