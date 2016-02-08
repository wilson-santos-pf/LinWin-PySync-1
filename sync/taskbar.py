import wx

from threading import Thread
from sysconfig import get_path
from os.path import join
from logging import getLogger
from threading import Event

from . import gui
from .gui import main


class LocalBoxIcon(wx.TaskBarIcon):

    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE = wx.NewId()
    TBMENU_CHANGE = wx.NewId()
    TBMENU_REMOVE = wx.NewId()
    TBMENU_GUI = wx.NewId()
    TBMENU_SYNC = wx.NewId()
    icon_path = None

    def __init__(self, waitevent=None, sites=None):
        location = SITESINI_PATH
        configparser = ConfigParser()
        configparser.read(location)
        gui = Gui(configparser=configparser, siteslist=sites)

        self.guievent = Event()
        self.guithread = Thread(target=gui.main, args=[gui, self.guievent, sites])
        self.guithread.daemon = True
        self.started = False
        wx.TaskBarIcon.__init__(self)
        if sites != None:
            self.sites = sites
        else:
            self.sites = []
        # The purpose of this 'frame' is to keep the mainloop of wx alive
        # (which checks for living wx thingies)
        self.frame = wx.Frame(parent=None)
        self.frame.Show(False)
        self.event = waitevent

        # Set the image
        self.taskbar_icon = wx.Icon(self.iconpath())

        self.SetIcon(self.taskbar_icon, "Test")

        # bind some events
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
        self.Bind(wx.EVT_MENU, self.start_gui, id=self.TBMENU_GUI)
        self.Bind(wx.EVT_MENU, self.start_sync, id=self.TBMENU_SYNC)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)
        self.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self.OnTaskBarLeftClick)

    def iconpath(self):
        return join(get_path('data'), 'localbox', 'localbox.ico')

    def start_gui(self, event):  # pylint: disable=W0613
        getLogger('taskbar').debug("Starting GUI")
        getLogger('taskbar').debug("GUI thread defined, starting it")
        if not self.started:
            self.guithread.start()
        getLogger('taskbar').debug("Setting event for gui to start")
        self.guievent.set()
        getLogger('taskbar').debug("GUI thread should be running")
        self.gui.deiconify()
        getLogger('taskbar').debug("GUI should be shown")


    def start_sync(self):
        self.event.set()

    def create_popup_menu(self):
        """
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.  Just create
        the menu how you want it and return it from this function,
        the base class takes care of the rest.
        """
        menu = wx.Menu()
        menu.Append(self.TBMENU_GUI, "Instellingen")
        # TODO: 'force sync'/'wait sync' dependant on lock status
        menu.AppendSeparator()
        menu.Append(self.TBMENU_SYNC, "Force Sync")
        menu.AppendSeparator()
        menu.Append(self.TBMENU_CLOSE, "Afsluiten")
        return menu

    def OnTaskBarActivate(self, event):  # pylint: disable=W0613
        """"""
        pass

    def OnTaskBarClose(self, event):  # pylint: disable=W0613
        """
        Destroy the taskbar icon and frame from the taskbar icon itself
        """
        self.frame.Close()
        self.started = False
        exit(1)

    def OnTaskBarLeftClick(self, event):  # pylint: disable=W0613
        """
        Create the taskbar-click menu
        """
        menu = self.create_popup_menu()
        self.PopupMenu(menu)
        menu.Destroy()


def taskbarmain(waitevent=None, sites=None):
    app = wx.App(False)
    LocalBoxIcon(waitevent, sites=sites)
    app.MainLoop()
