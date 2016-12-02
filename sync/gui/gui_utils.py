import wx
from sys import prefix as sys_prefix
from os.path import join, exists
from sysconfig import get_path
from os import getcwd

from sync._version import __version__

MAIN_FRAME_SIZE = (700, 550)
MAIN_PANEL_SIZE = (MAIN_FRAME_SIZE[0], 350)
PASSPHRASE_DIALOG_SIZE = (500, 300)
NEW_SYNC_DIALOG_SIZE = (500, 240)
NEW_SYNC_WIZARD_SIZE = (500, 100)
NEW_SYNC_PANEL_SIZE = (NEW_SYNC_DIALOG_SIZE[0], 145)
MAIN_TITLE = 'YourLocalBox %s' % __version__
PASSPHRASE_TITLE = 'YourLocalBox %s - Enter Passphrase' % __version__
DEFAULT_BORDER = 10


def iconpath():
    """
    returns the path for the icon related to this widget
    """
    ico_path = join(sys_prefix, 'localbox', 'localbox.ico')
    if exists(ico_path):
        return ico_path
    else:
        return join('data', 'icon', 'localbox.ico')


def is_valid_input(value):
    return value is not None and value.strip()


def show_error_dialog(message, title, standalone=False):
    if standalone:
        app = wx.App()
    wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)


def select_directory(cwd=getcwd()):
    dialog = wx.DirDialog(None, _("Choose a file"), style=wx.DD_DEFAULT_STYLE, defaultPath=cwd,
                          pos=(10, 10))
    if dialog.ShowModal() == wx.ID_OK:
        selected_dir = dialog.GetPath()
        return selected_dir

    dialog.Destroy()
