'''
Module that defines the settings dialog
'''

import gtk
from lox.config import settings, load, save, AUTHTYPES, LOGLEVELS
from lox.gui.gnome.icon import icon


class SettingsDialog(gtk.Dialog):

    def __init__(self):
        super(SettingsDialog,self).__init__("Localbox password", None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.connect("response", self.response)
        self.set_title("Session settings")
        self.set_icon_from_file(icon(size=64))
        self.set_border_width(10)
        self.set_size_request(640,380)
        self.set_position(gtk.WIN_POS_MOUSE)

        self._name = None

        layout = gtk.Table(10, 2, False)
        layout.set_col_spacings(3)
        self.vbox.pack_start(layout)

        # settings
        label_session = gtk.Label("Session name:")
        label_session.set_alignment(0, 0.5)
        self._session = gtk.Entry()
        layout.attach(label_session,0,1,0,1)
        layout.attach(self._session,1,2,0,1)

        label_dir = gtk.Label("Local folder to synchronize:")
        label_dir.set_alignment(0, 0.5)
        self._dir = gtk.Entry()
        layout.attach(label_dir,0,1,1,2)
        layout.attach(self._dir,1,2,1,2)

        label_url = gtk.Label("Localbox URL:")
        label_url.set_alignment(0, 0.5)
        self._url = gtk.Entry()
        layout.attach(label_url,0,1,2,3)
        layout.attach(self._url,1,2,2,3)

        label_auth = gtk.Label("Authentication:")
        label_auth.set_alignment(0, 0.5)
        self._auth = gtk.combo_box_new_text()
        for i in AUTHTYPES:
            self._auth.append_text(i)
        layout.attach(label_auth,0,1,3,4)
        layout.attach(self._auth,1,2,3,4)

        label_username = gtk.Label("Username:")
        label_username.set_alignment(0, 0.5)
        self._username = gtk.Entry()
        layout.attach(label_username,0,1,4,5)
        layout.attach(self._username,1,2,4,5)

        label_password = gtk.Label("Password:")
        label_password.set_alignment(0, 0.5)
        self._password = gtk.Entry()
        layout.attach(label_password,0,1,5,6)
        layout.attach(self._password,1,2,5,6)

        label_interval = gtk.Label("Refresh interval (seconds)")
        label_interval.set_alignment(0, 0.5)
        self._interval = gtk.Entry()
        layout.attach(label_interval,0,1,6,7)
        layout.attach(self._interval,1,2,6,7)

        label_loglevel = gtk.Label("Log level")
        label_loglevel.set_alignment(0, 0.5)
        self._loglevel = gtk.combo_box_new_text()
        for i in LOGLEVELS:
            self._loglevel.append_text(i)
        layout.attach(label_loglevel,0,1,7,8)
        layout.attach(self._loglevel,1,2,7,8)

        # separator
        line = gtk.HSeparator()
        layout.attach(line,0,2,8,9)

        layout.show_all()

    def do_load(self,name = None):
        if name is None:
            self._name is None
            self._session.set_text('')
            self._dir.set_text('')
            self._url.set_text('')
            self._auth.set_active(0)
            self._username.set_text('')
            self._password.set_text('')
            self._interval.set_text('300') # five minutes
            self._loglevel.set_active(2) # warn
        else:
            self._name = name # keep track of original name in case it is changed
            self._session.set_text(name)
            self._dir.set_text(settings[name]['local_dir'])
            self._url.set_text(settings[name]['lox_url'])
            try:
                auth_type = AUTHTYPES.index(settings[name]['auth_type'])
                self._auth.set_active(auth_type)
            except ValueError:
                self._auth.set_active(0)
            self._username.set_text(settings[name]['username'])
            self._password.set_text(settings[name]['password'])
            self._interval.set_text(settings[name]['interval'])
            try:
                level = LOGLEVELS.index(settings[name]['log_level'])
                self._loglevel.set_active(level)
            except ValueError:
                self._loglevel.set_active(2) # warn

    def response(self, widget, response):
        if response == gtk.RESPONSE_ACCEPT:
            global config
            print 'clicked on okay'
            # save settings
            name = self._session.get_text()
            d = dict()
            d['local_dir'] = self._dir.get_text()
            d['lox_url'] = self._url.get_text()
            d['auth_type'] = AUTHTYPES[self._auth.get_active()]
            d['username'] = self._username.get_text()
            d['password'] = self._password.get_text()
            d['interval'] = self._interval.get_text()
            d['log_level'] = LOGLEVELS[self._loglevel.get_active()]
            try:
                if not (self.name is None):
                    settings.pop(self._name)
                settings[name] = d
                save()
            except Exception as e:
                lox.gui.gnome.messagebox(ERROR,"Cannot save settings: {0}".format(str(e)))
                return True
        self.destroy()

    def run(self):
        result = super(SettingsDialog, self).run()
        return result

