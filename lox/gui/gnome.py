'''

Usage:

    import lox.gui_gnome as gui

    gui.mainloop()

Dependencies:

    sudo apt-get install python-appindicator
    sudo apt-get install python-notify

'''
import os
import sys
import gtk
import gobject
import pynotify
import subprocess
import lox.config
if os.getenv('DESKTOP_SESSION').lower() == 'ubuntu':
    import appindicator


AUTHTYPES = ["localbox"]
LOGLEVELS = ["none","error","warn","info","debug","traffic"]

INFO = gtk.MESSAGE_INFO
ERROR = gtk.MESSAGE_ERROR

def icon(ref='localbox',size=32):
    this = os.path.realpath(__file__)
    path = os.path.dirname(this)
    filename = '{0}_{1}.png'.format(ref,size)
    full_path = os.path.join(path,filename)
    return full_path

class ConfigWindow(gtk.Window):

    def __init__(self):
        super(ConfigWindow,self).__init__()
        self.set_title("LocalBox sessions")
        self.set_icon_from_file(icon(size=64))
        self.connect('delete_event',self.delete_event)
        self.connect('destroy',self.on_destroy)
        self.set_border_width(10)
        self.set_size_request(640,320)
        self.set_position(gtk.WIN_POS_CENTER)

        self._selected_session = None

        layout = gtk.Table(4, 2, False)
        layout.set_col_spacings(3)
        self.add(layout)

        # session liststore
        self._liststore = gtk.ListStore(gobject.TYPE_STRING)
        for session in lox.config.settings.iterkeys():
            self._liststore.append([session])

        # session listview
        self._treeview = gtk.TreeView(self._liststore)
        #self._treeview.set_headers_visible(False)
        self._selection = self._treeview.get_selection()
        self._selection.set_mode(gtk.SELECTION_SINGLE)
        self._selection.connect("changed", self._select)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Session name', cell)
        column.set_cell_data_func(cell, self._update_cell) # function to update the cell
        self._treeview.append_column(column)
        layout.attach(self._treeview, 0, 1, 1, 2, gtk.FILL | gtk.EXPAND,
            gtk.FILL | gtk.EXPAND, 1, 1)


        # title (row 0-1, column = 0-2)
        #title = gtk.Label("Sessions:")
        #halign = gtk.Alignment(0, 0, 0, 0)
        #halign.add(title)
        #layout.attach(halign, 0, 2, 0, 1, gtk.FILL,
        #    gtk.FILL, 0, 0);

        # buttons right
        self._add = gtk.Button("Add")
        self._add.connect('clicked', self.on_add, None)

        self._edit = gtk.Button("Edit")
        self._edit.set_sensitive(False)
        self._edit.connect('clicked', self.on_edit, None)

        self._delete = gtk.Button("Remove")
        self._delete.set_sensitive(False)
        self._delete.connect('clicked', self.on_delete, None)

        buttoncol = gtk.VButtonBox()
        buttoncol.set_layout(gtk.BUTTONBOX_START)
        buttoncol.add(self._add)
        buttoncol.add(self._edit)
        buttoncol.add(self._delete)
        layout.attach(buttoncol,1,2,1,2, gtk.SHRINK, gtk.EXPAND|gtk.FILL,16,8)

        # separator
        line = gtk.HSeparator()
        layout.attach(line,0,2,2,3,gtk.EXPAND|gtk.FILL,gtk.SHRINK,0,8)

        # buttons bottom
        close = gtk.Button("Close")
        close.connect('clicked', self.on_close, None)

        buttonrow = gtk.HButtonBox()
        buttonrow.set_layout(gtk.BUTTONBOX_END)
        buttonrow.add(close)
        layout.attach(buttonrow,0,2,7,8,gtk.EXPAND|gtk.FILL,gtk.SHRINK,0,0)

    def _update_cell(self, column, cell, model, iter):
        session_name = model.get_value(iter, 0)
        cell.set_property('text',session_name)
        return

    def _select(self,selected):
        self._edit.set_sensitive(True)
        self._delete.set_sensitive(True)
        (model, pathlist) = self._selection.get_selected_rows()
        for path in pathlist :
            tree_iter = model.get_iter(path)
            self._selected_session = model.get_value(tree_iter,0)

    def do_refresh(self):
        self._liststore.clear()
        for session in lox.config.settings.iterkeys():
            self._liststore.append([session])

    def do_show(self):
        self.do_refresh()
        self.show_all()

    def delete_event(self, widget, event, data=None):
        self.hide()
        return True

    def on_add(self, widget, obj):
        settings_window.do_load(None)
        settings_window.do_show()

    def on_edit(self, widget, obj):
        settings_window.do_load(self._selected_session)
        settings_window.do_show()

    def on_delete(self, widget, obj):
        lox.config.settings.pop(self._selected_session)
        lox.config.save()
        self.do_refresh()

    def on_destroy(self, widget, obj):
        # hide window, do not destroy
        self.hide()
        return True

    def on_close(self, widget, obj):
        # hide window, do not destroy
        self.hide()
        return True

class SettingsWindow(gtk.Window):

    def __init__(self):
        super(SettingsWindow,self).__init__()
        self.set_title("Session settings")
        self.set_icon_from_file(icon(size=64))
        self.connect('delete_event',self.delete_event)
        self.connect('destroy',self.on_destroy)
        self.set_border_width(10)
        self.set_size_request(640,320)

        self._name = None

        layout = gtk.Table(10, 2, False)
        layout.set_col_spacings(3)
        self.add(layout)

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

        # buttons
        cancel = gtk.Button("Cancel")
        cancel.connect('clicked', self.on_cancel, None)

        okay = gtk.Button("OK")
        okay.connect('clicked', self.on_okay, None)

        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        buttonbox.add(cancel)
        buttonbox.add(okay)
        layout.attach(buttonbox,0,2,9,10)

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
            self._dir.set_text(lox.config.settings[name]['local_dir'])
            self._url.set_text(lox.config.settings[name]['lox_url'])
            try:
                auth_type = AUTHTYPES.index(lox.config.settings[name]['auth_type'])
                self._auth.set_active(auth_type)
            except ValueError:
                self._auth.set_active(0)
            self._username.set_text(lox.config.settings[name]['username'])
            self._password.set_text(lox.config.settings[name]['password'])
            self._interval.set_text(lox.config.settings[name]['interval'])
            try:
                level = LOGLEVELS.index(lox.config.settings[name]['log_level'])
                self._loglevel.set_active(level)
            except ValueError:
                self._loglevel.set_active(2) # warn


    def do_show(self):
        self.show_all()

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        self.hide()
        return True

    def on_destroy(self, widget, obj):
        print 'clicked on destroy'
        self.hide()
        return True

    def on_cancel(self, widget, obj):
        print 'clicked on cancel'
        self.hide()
        return True

    def on_okay(self, widget, obj):
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
        d['log_level'] = self._loglevel.get_text()
        try:
            if not (self.name is None):
                lox.config.settings.pop(self._name)
            lox.config.settings[name] = d
            lox.config.save()
        except Exception as e:
            messagebox(ERROR,"Cannot save settings: {0}".format(str(e)))
            return True
        else:
            # refresh
            config_window.do_refresh()
            self.hide()
            return True

class GtkIndicator():
    def __init__(self):
        self.tray = gtk.StatusIcon()
        self.tray.set_title('lox-client')
        self.tray.set_from_file(icon(size=32))
        self.tray.connect('popup-menu', self._on_right_click)
        self.tray.set_tooltip(('LocalBox sync client'))

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

        for session in lox.config.settings.iterkeys():
            item_open = gtk.MenuItem("Open folder '{0}'".format(session))
            item_open.connect('activate',self._open,session)
            item_open.show()
            self.append(item_open)
        s = gtk.SeparatorMenuItem()
        s.show()
        self.append(s)
        item1 = gtk.MenuItem("Uitnodigingen")
        item1.connect('activate',self._invitations)
        item1.show()
        self.append(item1)
        item2 = gtk.MenuItem("Configuratie")
        item2.connect('activate',self._configure)
        item2.show()
        self.append(item2)
        item3 = gtk.MenuItem("Help")
        item3.connect('activate',self._help)
        item3.show()
        self.append(item3)
        s = gtk.SeparatorMenuItem()
        s.show()
        self.append(s)
        item4 = gtk.MenuItem("Afsluiten")
        item4.connect('activate',self._close)
        item4.show()
        self.append(item4)

    def _open(self,obj,session):
        try:
            path = lox.config.settings[session]['local_dir']
            fullpath = os.path.expanduser(path)
            subprocess.call(['gnome-open',fullpath])
        except Exception as e:
            messagebox(ERROR,"Cannot open folder: {0}".format(str(e)))

    def _invitations(self,obj):
        messagebox(INFO, "Handling invitations is not yet implemented. Use the web interface instead.")

    def _help(self,obj):
        messagebox(INFO,"Help not yet implemented. Will be added later.")

    def _configure(self,obj):
        config_window.do_refresh()
        config_window.do_show()

    def _close(self,obj):
        gtk.main_quit()

def notify(title,message):
    pynotify.init("LocalBox")
    n = pynotify.Notification(title,message,icon(size=64))
    #n.set_icon_from_pixbuf()
    n.set_timeout(2000)
    if not n.show():
        print "failed to send notification"

def messagebox(icon, message):
    m = gtk.MessageDialog(None,
            gtk.DIALOG_DESTROY_WITH_PARENT, icon,
            gtk.BUTTONS_CLOSE, message)
    m.run()
    m.destroy()

def mainloop():
    global config_window
    global settings_window
    gobject.threads_init()
    if os.getenv('DESKTOP_SESSION').lower() == 'ubuntu':
        indicator = UnityIndicator()
    else:
        indicator = GtkIndicator()
    config_window = ConfigWindow()
    settings_window = SettingsWindow()
    notify("LocalBox","Sync is running")
    gtk.main()
    indicator.destroy()
