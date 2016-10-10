import wx
from os.path import join
from sysconfig import get_path

from sync.version import VERSION


def iconpath():
    """
    returns the path for the icon related to this widget
    """
    return join(get_path('data'), 'localbox', 'localbox.ico')


def is_valid_input(value):
    return value is not None and value.strip()


def show_error_dialog(message, title):
    wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)


MAIN_FRAME_SIZE = (550, 550)
MAIN_PANEL_SIZE = (MAIN_FRAME_SIZE[0], 350)
NEW_SYNC_DIALOG_SIZE = (500, 240)
NEW_SYNC_WIZARD_SIZE=(500, 100)
NEW_SYNC_PANEL_SIZE = (NEW_SYNC_DIALOG_SIZE[0], 145)
MAIN_TITLE = 'YourLocalBox %s' % VERSION
NEW_SYNC_DIALOG_TITLE = 'Add new sync'
DEFAULT_BORDER = 10


class WizardStep():
    def __init__(self, next_panel, next_function):
        self.next_panel = next_panel
        self.next_function = next_function

    def show_next_panel(self):
        self.next_panel.Show()

    def show_previous_panel(self):
        self.next_panel.Hide()

    def call_next_function(self):
        return self.next_function()