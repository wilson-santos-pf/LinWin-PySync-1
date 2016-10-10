import wx
import wx.wizard
from logging import getLogger

import pkg_resources
from sync.controllers.account_ctrl import AccountController
from sync.controllers.localbox_ctrl import SyncsController
from sync.controllers.preferences_ctrl import ctrl as preferences_ctrl
from sync.defaults import DEFAULT_LANGUAGE
from sync.gui import gui_utils
from sync.gui.gui_utils import MAIN_FRAME_SIZE, MAIN_PANEL_SIZE, \
    MAIN_TITLE, DEFAULT_BORDER
from sync.gui.wizard import NewSyncWizard
from sync.language import LANGUAGES


class Gui(wx.Frame):
    def __init__(self, parent):
        super(Gui, self).__init__(parent,
                                  title=MAIN_TITLE,
                                  size=MAIN_FRAME_SIZE,
                                  style=wx.CLOSE_BOX | wx.CAPTION)

        # Attributes
        self.toolbar_panels = dict()
        self.panel_syncs = SyncsPanel(self)
        self.panel_account = AccountPanel(self)
        self.panel_preferences = PreferencesPanel(self)
        self.panel_bottom = BottomPanel(self)
        self.panel_line = wx.Panel(self)

        line_sizer = wx.BoxSizer(wx.VERTICAL)
        line_sizer.Add(wx.StaticLine(self.panel_line, -1), 0, wx.ALL | wx.EXPAND, border=10)
        self.panel_line.SetSizer(line_sizer)

        self.ctrl = self.panel_syncs.ctrl

        self.panel_account.Hide()
        self.panel_preferences.Hide()

        bSizer1 = wx.BoxSizer(wx.VERTICAL)
        bSizer1.Add(self.panel_line, 0, wx.EXPAND, border=10)
        bSizer1.Add(self.panel_syncs, 0, wx.EXPAND, 10)
        bSizer1.Add(self.panel_account, 0, wx.EXPAND, 10)
        bSizer1.Add(self.panel_preferences, 0, wx.EXPAND, 10)
        bSizer1.Add(self.panel_bottom, 0, wx.ALIGN_BOTTOM, 10)

        self.SetSizer(bSizer1)

        self.InitUI()

        self.SetAutoLayout(True)
        self.SetSizer(bSizer1)
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def InitUI(self):

        self.add_toolbar()

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Bitmap(gui_utils.iconpath(), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

    def on_close(self, event):
        self.Hide()
        event.Veto(True)

    def add_toolbar(self):
        self.toolbar = self.CreateToolBar(style=wx.TB_TEXT)

        self.toolbar.AddStretchableSpace()
        stream = pkg_resources.resource_stream('sync.resources.images', 'sync.png')
        bt_toolbar_localboxes = self.toolbar.AddLabelTool(wx.ID_ANY, _('Syncs'), wx.BitmapFromImage(
            wx.ImageFromStream(
                stream,
                wx.BITMAP_TYPE_PNG
            )
        ))
        stream = pkg_resources.resource_stream('sync.resources.images', 'user.png')
        bt_toolbar_account = self.toolbar.AddLabelTool(wx.ID_ANY, _('Account'), wx.BitmapFromImage(
            wx.ImageFromStream(
                stream,
                wx.BITMAP_TYPE_PNG
            )
        ))
        stream = pkg_resources.resource_stream('sync.resources.images', 'preferences.png')
        bt_toolbar_preferences = self.toolbar.AddLabelTool(wx.ID_ANY, _('Preferences'), wx.BitmapFromImage(
            wx.ImageFromStream(
                stream,
                wx.BITMAP_TYPE_PNG
            )
        ))
        self.toolbar.AddStretchableSpace()

        self.toolbar.Realize()

        self.toolbar.EnableTool(bt_toolbar_localboxes.Id, False)

        self.toolbar_panels[bt_toolbar_localboxes.Id] = self.panel_syncs
        self.toolbar_panels[bt_toolbar_account.Id] = self.panel_account
        self.toolbar_panels[bt_toolbar_preferences.Id] = self.panel_preferences

        self.Bind(wx.EVT_TOOL, self.OnToolbarLocalboxesClick, id=bt_toolbar_localboxes.Id)
        self.Bind(wx.EVT_TOOL, self.OnToolbarLocalboxesClick, id=bt_toolbar_account.Id)
        self.Bind(wx.EVT_TOOL, self.OnToolbarLocalboxesClick, id=bt_toolbar_preferences.Id)

    def OnQuit(self, e):
        self.Close()

    def OnToolbarLocalboxesClick(self, event):
        for i in range(0, self.toolbar.GetToolsCount()):
            tool = self.toolbar.GetToolByPos(i)
            if tool.Id == event.Id:
                self.toolbar.EnableTool(tool.Id, False)
            else:
                self.toolbar.EnableTool(tool.Id, True)

        for item in self.toolbar_panels.items():
            if item[0] == event.Id:
                item[1].Show()
                self.ctrl = item[1].ctrl
            else:
                item[1].Hide()

        self.Layout()


# ----------------------------------- #
# ----       MAIN PANELS         ---- #
# ----------------------------------- #
class SyncsPanel(wx.Panel):
    """
    Custom Panel containing a ListCtrl to list the syncs/localboxes
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, size=MAIN_PANEL_SIZE)
        # Attributes
        self.ctrl = LocalboxListCtrl(self)
        self.btn_add_localbox = wx.Button(self, label=_('Add'), size=(70, 30))
        self.btn_delete = wx.Button(self, label=_('Delete'), size=(70, 30))

        # Layout
        self._DoLayout()

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.newSyncDialog, self.btn_add_localbox)
        self.Bind(wx.EVT_BUTTON, self.ctrl.delete, self.btn_delete)

        # Setup
        self.ctrl.populate_list()

    def _DoLayout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(self.ctrl, proportion=1, flag=wx.EXPAND)
        vbox.Add(hbox3, proportion=1, flag=wx.LEFT | wx.RIGHT | wx.EXPAND,
                 border=10)

        vbox.Add((-1, 25))

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(self.btn_add_localbox)
        hbox4.Add(self.btn_delete)
        vbox.Add(hbox4, flag=wx.ALIGN_RIGHT | wx.RIGHT, border=10)

        vbox.Add((-1, 25))

        self.SetSizer(vbox)

    def newSyncDialog(self, event):
        # NewSyncDialog(parent=self, ctrl=self.ctrl).Show()
        wizard = NewSyncWizard(self.ctrl)


class AccountPanel(wx.Panel):
    """

    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, size=MAIN_PANEL_SIZE)

        # Attributes
        self.ctrl = AccountController()
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(self, label=_("Hi, User!!!")),
                  1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=DEFAULT_BORDER)

        self.SetSizer(sizer)


class PreferencesPanel(wx.Panel):
    """

    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, size=MAIN_PANEL_SIZE)

        # Attributes
        self.ctrl = preferences_ctrl
        self.language_choice = wx.Choice(self, choices=LANGUAGES.keys())

        self.language_choice.SetSelection(self.language_choice.FindString(
            self.ctrl.prefs.language if (self.ctrl.prefs.language is not None) else DEFAULT_LANGUAGE))

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(self, label=_("Language")),
                  flag=wx.EXPAND | wx.ALL, border=10)
        sizer.Add(self.language_choice, flag=wx.EXPAND | wx.ALL, border=10)

        sizer.Add(wx.StaticLine(self, -1), 0, wx.ALL | wx.EXPAND, border=10)

        self.SetSizer(sizer)

        self.language_choice.Bind(wx.EVT_CHOICE, self.OnChoice)

    def OnChoice(self, event):
        language_selected = self.language_choice.GetString(self.language_choice.GetSelection())
        getLogger(__name__).debug(
            "You selected " + language_selected + " from Choice")
        self.ctrl.prefs.language = language_selected


# ----------------------------------- #
# ----       OTHER Panels        ---- #
# ----------------------------------- #
class LoginPanel(wx.Panel):
    def __init__(self, parent):
        super(LoginPanel, self).__init__(parent)

        # Attributes
        self.parent = parent
        self._username = wx.TextCtrl(self)
        self._password = wx.TextCtrl(self, style=wx.TE_PASSWORD)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        input_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer.Add(wx.StaticText(self, label=_("Username:")),
                        0, wx.ALL | wx.ALIGN_LEFT)
        input_sizer.Add(self._username, 0, wx.ALL | wx.EXPAND)
        input_sizer.Add(wx.StaticText(self, label=_("Password:")),
                        0, wx.ALL | wx.ALIGN_LEFT, border=DEFAULT_BORDER)
        input_sizer.Add(self._password, 0, wx.ALL | wx.EXPAND)

        main_sizer.Add(input_sizer, 1, wx.ALL | wx.EXPAND, border=DEFAULT_BORDER)

        self.SetSizer(main_sizer)

    def get_username(self):
        return self._username.GetValue()

    def get_password(self):
        return self._password.GetValue()


class BottomPanel(wx.Panel):
    """
    Custom Panel containing buttons: "Ok", "Apply" and "Cancel"
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, size=(MAIN_PANEL_SIZE[0], 500))

        # Attributes
        self.parent = parent
        self.btn_ok = wx.Button(self, id=wx.ID_OK, label=_('Ok'))
        self.btn_apply = wx.Button(self, id=wx.ID_APPLY, label=_('Apply'))
        self.btn_close = wx.Button(self, id=wx.ID_CLOSE, label=_('Close'))

        # Layout
        self._DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnClickOk, id=self.btn_ok.Id)
        self.Bind(wx.EVT_BUTTON, self.ApplyOnClick, id=self.btn_apply.Id)
        self.Bind(wx.EVT_BUTTON, self.CloseOnClick, id=self.btn_close.Id)

    def _DoLayout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_szr = wx.StdDialogButtonSizer()

        btn_szr.AddButton(self.btn_ok)
        btn_szr.AddButton(self.btn_apply)
        btn_szr.AddButton(self.btn_close)

        btn_szr.Realize()

        main_sizer.Add(wx.StaticLine(self, -1), 0, wx.ALL | wx.EXPAND, border=10)
        main_sizer.Add(btn_szr, border=10)
        self.SetSizer(main_sizer)

    def OnClickOk(self, event):
        getLogger(__name__).debug('OkOnClick')
        self.parent.ctrl.save()
        self.parent.Hide()

    def ApplyOnClick(self, event):
        getLogger(__name__).debug('ApplyOnClick')
        self.parent.ctrl.save()

    def CloseOnClick(self, event):
        getLogger(__name__).debug('CloseOnClick')
        self.parent.Hide()


# ----------------------------------- #
# ----     GUI Controllers       ---- #
# ----------------------------------- #
class LocalboxListCtrl(wx.ListCtrl):
    """
    This class behaves like a bridge between the GUI components and the real syncs controller.
    """

    def __init__(self, parent):
        super(LocalboxListCtrl, self).__init__(parent,
                                               style=wx.LC_REPORT)

        self.ctrl = SyncsController()

        # Add three columns to the list
        self.InsertColumn(0, _("Label"))
        self.InsertColumn(1, _("Path"))
        self.InsertColumn(2, _("URL"))

        self.SetColumnWidth(0, 100)
        self.SetColumnWidth(1, 250)
        self.SetColumnWidth(2, 200)

    def populate_list(self):
        """
        Read the syncs list from the controller
        """
        for item in self.ctrl.load():
            self.Append((item.label, item.path, item.url))

    def add(self, item):
        getLogger(__name__).debug('Add item: %s' % item)
        self.Append((item.label, item.path, item.url))
        self.ctrl.add(item)

    def delete(self, event):
        idx = 0
        while idx > -1:
            idx = self.GetNextSelected(-1)

            if idx > -1:
                getLogger(__name__).debug('Delete item: #%d' % idx)
                self.DeleteItem(idx)
                self.ctrl.delete(idx)

        self.save()

    def save(self):
        getLogger(__name__).info('Sync list ctrl save()')
        self.ctrl.save()


# ----------------------------------- #
# ----         Dialogs           ---- #
# ----------------------------------- #
class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        super(LoginDialog, self).__init__(parent=parent)

        # Attributes
        self.panel = LoginPanel(self)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetInitialSize()
