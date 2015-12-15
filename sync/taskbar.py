import wx

from sync import gui

class LocalBoxIcon(wx.TaskBarIcon):

    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE   = wx.NewId()
    TBMENU_CHANGE  = wx.NewId()
    TBMENU_REMOVE  = wx.NewId()
    TBMENU_GUI = wx.NewId()
 
    def __init__(self):
        wx.TaskBarIcon.__init__(self)
        # The purpose of this 'frame' is to keep the mainloop of wx alive (which checks for living wx thingies)
        self.frame = wx.Frame(parent=None)
        self.frame.Show(False)
 
        # Set the image
        self.tbIcon = wx.Icon('localbox.ico')
 
        self.SetIcon(self.tbIcon, "Test")
 
        # bind some events
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
        self.Bind(wx.EVT_MENU, self.StartGui, id=self.TBMENU_GUI)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)


    def StartGui(self, evt=None):
        gui.main()

    def CreatePopupMenu(self, evt=None):
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
        menu.Append(self.TBMENU_CLOSE,   "Exit Program")
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
        menu = self.CreatePopupMenu()
        self.PopupMenu(menu)
        menu.Destroy()

def taskbarmain():
   app = wx.App(False)
   icon = LocalBoxIcon()
   app.MainLoop()

#def testfunc(argument):
#    print "testfunc"
#    print argument
#    print "testfunc start"
#    gui.main()
#    print "end testfunc"

#app=wx.PySimpleApp(False)
#tb=wx.TaskBarIcon()
#icon = wx.Icon('qemu.ico')
#tb.SetIcon(icon)

#menu=wx.Menu()
#menu.append(
#wx.MenuItem("test")
#)

#wx.EVT_TASKBAR_LEFT_DCLICK(tb, testfunc)
#wx.EVT_TASKBAR_RIGHT_UP(tb, testfunc)

#app.MainLoop()
#print "after main"
#from time import sleep
#sleep(1000)
