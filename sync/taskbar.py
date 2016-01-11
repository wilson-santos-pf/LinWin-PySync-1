import wx

from sysconfig import get_path
from sync import gui
from os.path import join

class LocalBoxIcon(wx.TaskBarIcon):

    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE = wx.NewId()
    TBMENU_CHANGE = wx.NewId()
    TBMENU_REMOVE = wx.NewId()
    TBMENU_GUI = wx.NewId()
    icon_path = None

    def __init__(self):
        wx.TaskBarIcon.__init__(self)
        # The purpose of this 'frame' is to keep the mainloop of wx alive
        # (which checks for living wx thingies)
        self.frame = wx.Frame(parent=None)
        self.frame.Show(False)

        # Set the image
        self.taskbar_icon = wx.Icon(self.iconpath())

        self.SetIcon(self.taskbar_icon, "Test")

        # bind some events
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
        self.Bind(wx.EVT_MENU, self.start_gui, id=self.TBMENU_GUI)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)


    def iconpath(self):
        return join(get_path('data'), 'localbox', 'localbox.ico')


    def start_gui(self, evt=None):
        gui.main()


    def create_popup_menu(self, evt=None):
        """
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.  Just create
        the menu how you want it and return it from this function,
        the base class takes care of the rest.
        """
        menu = wx.Menu()
        menu.Append(self.TBMENU_GUI, "Open Configuratie gebruikers interface")
        # TODO: 'force sync'/'wait sync' dependant on lock status
        menu.AppendSeparator()
        menu.Append(self.TBMENU_CLOSE, "Exit Program")
        return menu

    def OnTaskBarActivate(self, evt):
        """"""
        pass

    #----------------------------------------------------------------------
    def OnTaskBarClose(self, evt):
        """
        Destroy the taskbar icon and frame from the taskbar icon itself
        """
        self.frame.Close()
        exit(1)

    #----------------------------------------------------------------------
    def OnTaskBarLeftClick(self, evt):
        """
        Create the right-click menu
        """
        menu = self.create_popup_menu()
        self.PopupMenu(menu)
        menu.Destroy()

def taskbarmain():
    app = wx.App(False)
    icon = LocalBoxIcon()
    app.MainLoop()
