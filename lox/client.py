'''

Main module

Usage:
    
    import client
    
    client.main()
    # or client.test() for a test run of the sync

Todo:
    
    Check if daemon runs as expected

'''

import os
import sys
import time
import traceback

import config
from api import LoxApi
from daemon import Daemon
from session import LoxSession
from error import LoxError

__author__ = "imtal@yolt.nl"
__copyright__ = "(C) 2014, see LICENSE file"
__version__ = "0.1"

def Msg(msg):
    print "\nLocalBox client: %s\n" % msg

restart = False

class Supervisor(Daemon):

    def started(self):
        global restart
        if restart:
            restart = False
            Msg("started")

    def run(self, interactive = False):
        for Name in config.sessions():
            t = LoxSession(Name, interactive = interactive)
            t.start()

def need_sessions():
    if len(config.sessions())==0:
        Msg("no sessions configured, edit ~/.lox/lox-client.conf")
        sys.exit(1)

def main():
    Action = sys.argv[1].lower() if len(sys.argv)>1 else 'undefined'
    path = os.environ['HOME']
    pidfile = os.environ['HOME']+'/.lox/lox-client.pid'
    logfile = open(os.environ['HOME']+'/.lox/lox-client.log','w+')
    daemon = Supervisor(pidfile, path=os.environ['HOME'], umask=100) #, stdout=logfile, stderr=logfile, preserve=[logfile])
    try:
        if Action=='start':
            need_sessions()
            Msg("started")
            daemon.start()
        elif Action=='stop':
            daemon.stop()
            Msg("stopped")
        elif Action=='run':
            Msg("run in foreground")
            daemon.run(interactive = True)
        elif Action=='restart':
            daemon.restart()
        elif Action=='status':
            s = daemon.status()
            if s is None:
                Msg("not running ...")
            else:
                Msg("running with pid %s" % s)
        elif Action=='invitations':
            need_sessions()
            Msg("list invitations")
            for Name in config.sessions():
                Api = LoxApi(Name)
                Invitations = Api.invitations()
                print "%s: " % Name
                for Invite in Invitations:
                    Share = Invite[u'share']
                    Item = Share[u'item']
                    print "  [%s] %s (%s)" % (Invite[u'id'],Item[u'path'],Invite[u'state'])
                print ""
        elif Action=='help':
            Cmd = os.path.basename(sys.argv[0])
            Msg("desktop sync version {}".format(__version__))
            print "  Usage: {} [command]".format(Cmd)
            print ""
            print "       start       - starts the client"
            print "       stop        - stops the client"
            print "       run         - run in forground (interactive)"
            print "       restart     - reloads the confguration"
            print "       invitations - show invitations"
            #print "       sync        - force a synchronization" # must be done with a signal handler
            print "       status      - show the status of the client"
            print "       help        - show this help"
            sys.exit(0)
        else:
            Cmd = os.path.basename(sys.argv[0])
            print "\nUsage: %s start|stop|run|invitations|restart|status|help|... \n" % Cmd
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        Msg(e)
        traceback.print_exc()
        sys.exit(1)
