import wx
from os.path import join
from sysconfig import get_path

from sync.version import VERSION

MAIN_FRAME_SIZE = (550, 550)
MAIN_PANEL_SIZE = (MAIN_FRAME_SIZE[0], 350)
PASSPHRASE_DIALOG_SIZE = (500, 300)
NEW_SYNC_DIALOG_SIZE = (500, 240)
NEW_SYNC_WIZARD_SIZE = (500, 100)
NEW_SYNC_PANEL_SIZE = (NEW_SYNC_DIALOG_SIZE[0], 145)
MAIN_TITLE = 'YourLocalBox %s' % VERSION
PASSPHRASE_TITLE = 'YourLocalBox %s - Enter Passphrase' % VERSION
NEW_SYNC_DIALOG_TITLE = 'Add new sync'
DEFAULT_BORDER = 10


def iconpath():
    """
    returns the path for the icon related to this widget
    """
    return join(get_path('data'), 'localbox', 'localbox.ico')


def is_valid_input(value):
    return value is not None and value.strip()


def show_error_dialog(message, title, standalone=False):
    if standalone:
        app = wx.App()
    wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)


def ask_passphrase(localbox_client, dialog):
    username = localbox_client.authenticator.username
    label = localbox_client.authenticator.label

    app = wx.App()
    dialog.show(username=username, label=label)
    app.MainLoop()
