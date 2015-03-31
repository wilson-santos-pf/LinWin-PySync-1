'''
Module that defines the systray indicator class
for both Unity and Gnome like operating systems

'''

import os
import gtk
import subprocess
from lox.config import settings
from lox.gui.gnome.messagebox import messagebox, INFO, ERROR
from lox.gui.gnome.icon import icon
from lox.gui.gnome.config_dialog import ConfigDialog
from lox.gui.gnome.settings_dialog import SettingsDialog
from lox.gui.gnome.password_dialog import PasswordDialog
import gettext
_ = gettext.gettext



if os.getenv('DESKTOP_SESSION').lower() == 'ubuntu':
    import appindicator

class GtkIndicator():
    def __init__(self):
        self.tray = gtk.StatusIcon()
        self.tray.set_title('lox-client')
        self.tray.set_from_file(icon(size=32))
        self.tray.connect('popup-menu', self._on_right_click)
        self.tray.set_tooltip(_('LocalBox sync client'))

    def destroy(self):
        self.tray.set_visible(False)

    def _on_right_click(self, icon, event_button, event_time):
        self._make_menu(event_button, event_time)

    def _make_menu(self, event_button, event_time):
        menu = IndicatorMenu()
        menu.popup(None, None, gtk.status_icon_position_menu,
                   event_button, event_time, self.tray)

class UnityIndicator():

    def __init__(self):
        self.ind = appindicator.Indicator(
                                'lox-client',
                                icon(size=16),
                                appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon("indicator-messages-new")

        menu = IndicatorMenu()
        self.ind.set_menu(menu)

    def destroy(self):
        # don't know how ...
        pass

class IndicatorMenu(gtk.Menu):

    def __init__(self):
        super(IndicatorMenu,self).__init__()

        for session in settings.iterkeys():
            item_open = gtk.MenuItem(_("Open folder '{0}'").format(session))
            item_open.connect('activate',self._open,session)
            item_open.show()
            self.append(item_open)
        s = gtk.SeparatorMenuItem()
        s.show()
        self.append(s)
        item1 = gtk.MenuItem(_("Invitations"))
        item1.connect('activate',self._invitations)
        item1.show()
        self.append(item1)
        item2 = gtk.MenuItem(_("Configuration"))
        item2.connect('activate',self._configure)
        item2.show()
        self.append(item2)
        item3 = gtk.MenuItem(_("Help"))
        item3.connect('activate',self._help)
        item3.show()
        self.append(item3)
        s = gtk.SeparatorMenuItem()
        s.show()
        self.append(s)
        item4 = gtk.MenuItem(_("Exit"))
        item4.connect('activate',self._close)
        item4.show()
        self.append(item4)

    def _open(self,obj,session):
        try:
            path = settings[session]['local_dir']
            fullpath = os.path.expanduser(path)
            subprocess.call(['gnome-open',fullpath])
        except Exception as e:
            messagebox(ERROR,_("Cannot open folder: {0}").format(str(e)))

    def _invitations(self,obj):
        messagebox(INFO,_("Handling invitations is not yet implemented. Use the web interface instead."))

    def _help(self,obj):
        messagebox(INFO,_("Help not yet implemented. Will be added later."))

    def _configure(self,obj):
        d = ConfigDialog()
        d.run()

    def _close(self,obj):
        gtk.main_quit()

class Indicator():

    def __init__(self):
        if os.getenv('DESKTOP_SESSION').lower() == 'ubuntu':
            self._indicator = UnityIndicator()
        else:
            self._indicator = GtkIndicator()

    def destroy(self):
        self._indicator.destroy()
