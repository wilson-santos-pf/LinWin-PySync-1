'''

Usage:

    import lox.gui_gnome as gui

    gui.mainloop()

'''
from getpass import getpass
from time import sleep

AUTHTYPES = ["localbox"]
LOGLEVELS = ["none","error","warn","info","debug","traffic"]

INFO = 1
ERROR = 2

def notify(message):
    sys.stderr.write(message)

def messagebox(icon,message):
    if icon==2:
        sys.stderr.write(message)
    else:
        sys.stdout.write(message)

def get_password():
    return getpass("Enter password to unlock: ")

def mainloop():
    try
    sleep(0.1)
    except KeyboardInterrupt as e:
    raise e

