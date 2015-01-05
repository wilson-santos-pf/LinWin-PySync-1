'''

Main module

Usage:

    import lox.client

    lox.client.main()

'''

import os
import sys
import time
import traceback

import lox.config as config
from lox.api import LoxApi
from lox.daemon import Daemon, DaemonError
from lox.session import LoxSession
from lox.error import LoxError
import lox.gui as gui


__author__ = "imtal@yolt.nl"
__copyright__ = "(C) 2014, see LICENSE file"
__version__ = "0.1"


def console_msg(msg):
    sys.stderr.write("\nLocalBox client: {0}\n\n".format(msg))
    sys.stderr.flush()


class Supervisor(Daemon):
    '''
    The daemon: start the sessions as threads and start the GUI
    '''
    sessions = dict()

    #def __init__(self,**kwargs):
    #    Daemon.__init__(self,kwargs)
    #    self.sessions = dict()

    def started(self, restart=False):
        if restart:
            console_msg("restarted")
        else:
            console_msg("started")

    def run(self, interactive = False):
        for name in config.settings.iterkeys():
            self.add(name, interactive)
        if not interactive:
            gui.mainloop()
            self.stop()

    def terminate(self):
        for name in self.sessions.iterkeys():
            self.remove(name)

    def add(self, name, interactive):
        self.sessions[name] = LoxSession(name, interactive)
        self.sessions[name].start()

    def remove(self, name):
        self.sessions[name].stop()
        del self.sessions[name]

    def restart(self,name):
        self.sessions[name].stop()
        while self.sessions[name].is_alive():
            pass
        self.sessions[name].start()


def need_sessions():
    '''
    Check if there are any sessions specified in config file
    '''
    if len(config.settings)==0:
        console_msg("no sessions configured, edit ~/.lox/lox-client.conf")
        sys.exit(1)

def cmd_start(daemon):
    '''
    Start the damon
    '''
    need_sessions()
    daemon.start()

def cmd_stop(daemon):
    '''
    Stop the daemon
    '''
    daemon.stop()
    console_msg("stopped")

def cmd_run(daemon):
    '''
    Run the deamon interactive in the foreground
    '''
    console_msg("run in foreground")
    daemon.run(interactive = True)

def cmd_restart(daemon):
    '''
    Restart daemon
    '''
    daemon.restart()

def cmd_status(daemon):
    '''
    Show status of daemon
    '''
    s = daemon.status()
    if s is None:
        console_msg("not running ...")
    else:
        console_msg("running with pid %s" % s)

def cmd_help(daemon):
    '''
    Show help
    '''
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
    '''
    Show invirtations for each session
    '''
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

def cmd_usage():
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
    '''
    Main routine: call routine from command
    '''
    cmd = sys.argv[1].lower() if len(sys.argv)>1 else cmd_usage()
    pidfile = os.environ['HOME']+'/.lox/lox-client.pid'
    logfile = os.environ['HOME']+'/.lox/lox-client.log'
    daemon = Supervisor(pidfile, path=os.environ['HOME'], umask=100, stdout=logfile, stderr=logfile)
    try:
        (func,description) = commands[cmd]
        func(daemon)
    except DaemonError as e:
        console_msg(e)
        sys.exit(1)
    except LoxError as e:
        console_msg(str(e))
        sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
