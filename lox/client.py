'''

Main module

Usage:
    
    import lox.client
    
    lox.client.main()

Todo:
    
    Check if daemon runs as expected

'''

import os
import sys
import time
import traceback

import lox.config as config
from lox.api import LoxApi
from lox.daemon import Daemon
from lox.session import LoxSession
from lox.error import LoxError
#import lox.gui as gui


__author__ = "imtal@yolt.nl"
__copyright__ = "(C) 2014, see LICENSE file"
__version__ = "0.1"


def console_msg(msg):
    print "\nLocalBox client: %s\n" % msg

restart = False

class Supervisor(Daemon):

    def started(self):
        global restart
        if restart:
            restart = False
            console_msg("started")

    def run(self, interactive = False):
        for Name in config.settings.iterkeys():
            t = LoxSession(Name, interactive = interactive)
            t.start()
        #gui.main()

def need_sessions():
    if len(config.settings)==0:
        console_msg("no sessions configured, edit ~/.lox/lox-client.conf")
        sys.exit(1)

def cmd_start(daemon):
    need_sessions()
    console_msg("started")
    daemon.start()
    
def cmd_stop(daemon):
    daemon.stop()
    console_msg("stopped")

def cmd_run(daemon):
    console_msg("run in foreground")
    daemon.run(interactive = True)

def cmd_restart(daemon):
    console_msg("restart")
    daemon.restart()

def cmd_status(daemon):
    s = daemon.status()
    if s is None:
        console_msg("not running ...")
    else:
        console_msg("running with pid %s" % s)

def cmd_help(daemon):
    cmd = os.path.basename(sys.argv[0])
    console_msg("desktop sync version {}".format(__version__))
    print "  Usage: {} [command]".format(cmd)
    print ""
    for c in commands.iterkeys():
        (f,description) = commands[c]
        print "       {0:12} - {1}".format(c,description)
    print ""
    sys.exit(0)

def cmd_invitations(daemon):
    need_sessions()
    console_msg("list invitations")
    for name in config.settings.iterkeys():
        api = LoxApi(name)
        invitations = api.invitations()
        print "%s: " % name
        for invite in invitations:
            share = invite[u'share']
            item = share[u'item']
            print "  [%s] %s (%s)" % (invite[u'id'],item[u'path'],invite[u'state'])
        print ""
    sys.exit(0)

def cmd_usage(daemon):
    cmd = os.path.basename(sys.argv[0])
    print "\nUsage: {0} start|stop|run|status|help|... \n".format(cmd)
    sys.exit(1)

commands = {
                "start": (cmd_start,"starts the client"),
                "stop": (cmd_stop,"stops the client"),
                "run": (cmd_run, "run in foreground (interactive)"),
                "restart": (cmd_restart, "reloads the confguration"),
                "status": (cmd_status,"show the status of the client"),
                "invitations": (cmd_invitations,"show invitations"),
                "help": (cmd_help,"show this help")
           }

def main():
    action = sys.argv[1].lower() if len(sys.argv)>1 else cmd_usage()
    path = os.environ['HOME']
    pidfile = os.environ['HOME']+'/.lox/lox-client.pid'
    logfile = open(os.environ['HOME']+'/.lox/lox-client.log','w+')
    daemon = Supervisor(pidfile, path=os.environ['HOME'], umask=100) #, stdout=logfile, stderr=logfile, preserve=[logfile])
    try:
        (f,description) = commands[action]
        f(daemon)
    except Exception as e:
        console_msg(e)
        traceback.print_exc()
        sys.exit(1)
