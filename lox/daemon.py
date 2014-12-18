import sys
import os
import time
import atexit
import signal

class DaemonError(Exception):
    def __init__(self,reason):
        self.value = reason
    def __str__(self):
        return repr(self.value)


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() and signal() methods
    """
    def __init__(self, pidfile, path='/', umask=0, stdin=None, stdout=None, stderr=None, preserve=[]):
        self.pidfile = pidfile
        devnull = os.devnull if (hasattr(os,"devnull")) else "/dev/null"
        stdin = devnull if (stdin is None) else stdin
        stdout = devnull if (stdout is None) else stdout
        stderr = devnull if (stderr is None) else stderr
        self.path = path
        self.umask = umask
        self.preserve = preserve

    def __daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        pid = os.fork()
        if pid > 0:
            # This is the first parent
            time.sleep(2)
            return
            #sys.exit(0)

        # Decouple from parent environment
        os.chdir(self.path)
        os.setsid()
        os.umask(self.umask)

        # do second fork
        pid = os.fork()
        if pid > 0:
            # This is the second parent
            sys.exit(0)

        # Close all open file descriptors
        import resource		# Resource usage information.
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024
        for fd in range(0, maxfd): # Iterate through and close all file descriptors
            if not fd in self.preserve:
                try:
                    os.close(fd)
                except OSError:	# On error, fd wasn't open to begin with (ignored)
                    pass

        # Redirect standard I/O file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Create the pidfile
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)

        # Register handler at exit
        atexit.register(self.__cleanup)

    def __cleanup(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            raise DaemonError('Already running')

        # Start the daemon
        self.__daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            raise DaemonError('Not running')

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as e:
            error = str(e)
            if error.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                raise DaemonError(error)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def status(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
            return pid
        except IOError:
            return None

    def run(self):
        """
        Override this method when you subclass Daemon. 
        It will be called after the process has been
        daemonized by start() or restart().
        """
        pass

    def terminate(self):
        """
        Override this method when you subclass Daemon.
        It will be called when the process is killed.
        """
        pass
