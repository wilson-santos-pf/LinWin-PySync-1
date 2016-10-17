"""
Modulemanaging a Windows Taskbar icon
"""
from logging import getLogger

from sync import language
from sync.controllers.preferences_ctrl import ctrl as preferences_ctrl
from sync.gui.gui_wx import Gui
from sync.defaults import SITESINI_PATH, LOCALE_PATH, VERSION
import sync.gui.gui_utils as gui_utils

try:
    import wx
except ImportError:
    getLogger(__name__).critical("Cannot import wx")

try:
    from ConfigParser import ConfigParser  # pylint: disable=F0401,E0611
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401,E0611


class LocalBoxIcon(wx.TaskBarIcon):
    """
    Class for managing a Windows taskbar icon
    """
    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE = wx.NewId()
    TBMENU_CHANGE = wx.NewId()
    TBMENU_REMOVE = wx.NewId()
    TBMENU_GUI = wx.NewId()
    TBMENU_SYNC = wx.NewId()
    TBMENU_SYNC2 = wx.NewId()
    TBMENU_VERSION = wx.NewId()
    TBMENU_DELETE_DECRYPTED = wx.NewId()
    icon_path = None

    def __init__(self, waitevent=None, sites=None):
        location = SITESINI_PATH
        configparser = ConfigParser()
        configparser.read(location)
        wx.TaskBarIcon.__init__(self)
        if sites is not None:
            self.sites = sites
        else:
            self.sites = []
        # The purpose of this 'frame' is to keep the mainloop of wx alive
        # (which checks for living wx thingies)
        self.frame = Gui(None)
        self.frame.Show(False)
        self.event = waitevent

        # Set the image
        self.taskbar_icon = wx.Icon(gui_utils.iconpath())

        self.SetIcon(self.taskbar_icon, gui_utils.MAIN_TITLE)

        # bind some events
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
        self.Bind(wx.EVT_MENU, self.start_gui, id=self.TBMENU_GUI)
        self.Bind(wx.EVT_MENU, self.start_sync, id=self.TBMENU_SYNC)
        self.Bind(wx.EVT_MENU, self.delete_decrypted, id=self.TBMENU_DELETE_DECRYPTED)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarClick)
        self.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self.OnTaskBarClick)

    def start_gui(self, event):  # pylint: disable=W0613
        """
        start the graphical user interface for configuring localbox
        """
        getLogger(__name__).debug("Starting GUI")
        self.frame.Show()
        self.frame.Raise()

    def start_sync(self, wx_event):  # pylint: disable=W0613
        """
        tell the syncer the system is ready to sync
        """
        if not self.event.is_set():
            self.event.set()
        else:
            getLogger(__name__).debug("Pressing start sync whilst sync in progress")

    def delete_decrypted(self, event):
        import sync
        sync.remove_decrypted_files()

    def create_popup_menu(self):
        """
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.  Just create
        the menu how you want it and return it from this function,
        the base class takes care of the rest.
        """
        getLogger(__name__).debug("create_popup_menu")
        menu = wx.Menu()
        menu.Append(self.TBMENU_GUI, _("Settings"))
        # TODO: 'force sync'/'wait sync' dependant on lock status
        menu.AppendSeparator()
        if self.event.is_set():
            menu.Append(self.TBMENU_SYNC2, _("Sync in progress"))
            menu.Enable(id=self.TBMENU_SYNC2, enable=False)
        else:
            menu.Append(self.TBMENU_SYNC, _("Force Sync"))

        menu.Append(self.TBMENU_DELETE_DECRYPTED, _("Delete decrypted files"))
        import desktop_utils.controllers.openfiles_ctrl as openfiles_ctrl
        if not openfiles_ctrl.load():
            menu.Enable(id=self.TBMENU_DELETE_DECRYPTED, enable=False)

        menu.AppendSeparator()

        menu.Append(self.TBMENU_VERSION, _("Version: %s") % VERSION)
        menu.Enable(id=self.TBMENU_VERSION, enable=False)

        menu.AppendSeparator()

        menu.Append(self.TBMENU_CLOSE, _("Quit"))
        return menu

    def OnTaskBarActivate(self, event):  # pylint: disable=W0613
        """required function for wxwidgets doing nothing"""
        pass

    def OnTaskBarClose(self, event):  # pylint: disable=W0613
        """
        Destroy the taskbar icon and frame from the taskbar icon itself
        """
        self.frame.Close()
        import sync
        sync.remove_decrypted_files()
        exit(1)

    def OnTaskBarClick(self, event):  # pylint: disable=W0613
        """
        Create the taskbar-click menu
        """
        menu = self.create_popup_menu()
        self.PopupMenu(menu)
        # menu.Destroy()


def taskbarmain(waitevent=None, sites=None):
    """
    main function to run to get the taskbar started
    """
    app = wx.App(False)
    language.set_language(preferences_ctrl.get_language_abbr())
    LocalBoxIcon(waitevent, sites=sites)
    app.MainLoop()
