from Tkinter import Tk
from Tkinter import Frame
from Tkinter import Label
from Tkinter import Entry
from Tkinter import Button
from Tkinter import Listbox
import tkFileDialog
from ttk import Combobox
from Tkinter import END
from ConfigParser import ConfigParser
from ConfigParser import NoOptionError
from .database import database_execute
from .localbox import LocalBox
from .auth import Authenticator
from .auth import AuthenticationError
from os.path import isdir

from threading import Event


class ConfigError(Exception):
    pass

class UsernameAndPasswordAsker(Tk):
    def __init__(self, parent=None):
        Tk.__init__(self, parent)
        self.title("Authentication Data")
        Label(self, text="username").grid(row=0, column=0)
        self.username = Entry(self)
        self.username.grid(row=0, column=1)
        Label(self, text="password").grid(row=1, column=0)
        self.password = Entry(self, show="*")
        self.password.grid(row=1, column=1)
        self.button = Button(master=self, text="something", command=self.stop_window)
        self.button.grid(row=2)
        self.lock = Event()

    def stop_window(self):
        self.lock.set()
        self.destroy()

    def __call__(self):
        self.mainloop()

class Gui(Tk):
    def __init__(self, parent=None, configparser=None):
        Tk.__init__(self, parent)
        self.configs = []
        self.button = Button(text="Add New", command=self.addNew)
        self.button.grid(row=0, column=0)
        self.configparser = configparser

    def add_entries(self, dataentryframe):
        self.configs.append(dataentryframe)
        position = len(self.configs)
        dataentryframe.grid(row=position, column=0)

    def addNew(self):
        de = DataEntry(self, '', '', '', '', self.configparser)
        self.add_entries(de)

def get_entry_fields(parent, text, value, row):
    label = Label(text=text, master=parent)
    label.grid(column=0, row=row)
    entry = Entry(master=parent)
    entry.insert(0, value)
    entry.grid(column=1, row=row)
    return entry

class DataEntry(Frame):
    def getfile(self):
        result = tkFileDialog.askdirectory()
        self.local_path.delete(0, END)
        self.local_path.insert(0, result)

    def __init__(self, master=None, name=None, url=None, localdir=None, direction=None, config=None):
        Frame.__init__(self, master=master, relief="raised", borderwidth=2)
        self.configparser = config
        self.orig_name = name
        self.site_name = get_entry_fields(self, "Sitename", name, 0)
        self.localbox_url = get_entry_fields(self, "LocalBox URL", url, 1)
        self.local_path = get_entry_fields(self, "Local Path", localdir, 2)
        self.lpbutton = Button(master=self, text="select directory", command=self.getfile)
        self.lpbutton.grid(column=2, row=2)
        

        label = Label(text="Direction", master=self)
        label.grid(column=0, row=3)
        self.sync_direction = Combobox(master=self)
        self.sync_direction['values'] = ['up', 'down', 'sync']
        self.sync_direction.grid(column=1, row=3)

        self.savebutton = Button(master=self, text="Save", command=self.save)
        self.savebutton.grid(row=4, column=0)
        self.authbutton = Button(master=self, text="Authenticate", command=self.authenticate)
        self.authbutton.grid(row=4, column=1)

    def save(self):
        try:
            if self.site_name.get() != self.orig_name:
                if self.site_name.get() in self.configparser.sections():
                    raise ConfigError("There is already a site with that name")
            if not isdir(self.local_path.get()):
                raise ConfigError("Share path needs to be a directory")
            if not self.sync_direction.get() in ['up', 'down', 'sync']:
                raise ConfigError("Direction needs to be either up, down or sync")
        

            if self.site_name.get() != self.orig_name:
                self.configparser.remove_section(self.orig_name)
                self.configparser.add_section(self.site_name.get())
                sql = "update sites set site=? where site=?;"
                database_execute(sql, (self.site_name.get(), self.orig_name))
                self.orig_name = self.site_name.get()
            self.configparser.set(self.site_name.get(), 'url', self.localbox_url.get())
            self.configparser.set(self.site_name.get(), 'path', self.local_path.get())
            self.configparser.set(self.site_name.get(), 'direction', self.sync_direction.get())
            with open('sites.ini', 'wb') as configfile:
                self.configparser.write(configfile)
            
            self.ew = Tk()
            self.ew.title("Success")
            Label(text="Config saved succesfully", master=self.ew).grid(row=0, column=0)
            Button(master=self.ew, text="close", command=self.closeExceptionWindow).grid(row=1, column=0)
        except ConfigError as e:
            self.ew = Tk()
            self.ew.title("error")
            Label(text=e.message, master=self.ew).grid(row=0, column=0)
            Button(master=self.ew, text="close", command=self.closeExceptionWindow).grid(row=1, column=0)

    def closeExceptionWindow(self):
        self.ew.destroy()

    def authenticate(self):
        localbox = LocalBox(self.localbox_url.get())
        authurl = localbox.get_authentication_url()
        authenticator = Authenticator(authurl, self.site_name.get())
        if not authenticator.has_client_credentials():
            credentials = UsernameAndPasswordAsker()
            credentials.__call__()
            credentials.lock.wait()
            # Show username/password field
            if authenticator.init_authenticate(credentials.username.get(), credentials.password.get()):
                print "succes"
            else:
                print "failure"
        else:
            try:
                authenticator.authenticate()
                print "credentials seem valid"
            except AuthenticationError:
                print "your credentials are invalidated"
def main():
    gui = Gui()
    gui.title('app')
    location='sites.ini'
    configparser = ConfigParser()
    configparser.read(location)
    sites = []
    for section in configparser.sections():
        try:
            dictionary = { 'name': section,
                'url': configparser.get(section, 'url'),
                'path': configparser.get(section, 'path'),
                'direction': configparser.get(section, 'direction')
            }
            sites.append(dictionary)

            de = DataEntry(gui, section, dictionary['url'], dictionary['path'], dictionary['direction'], configparser)
            gui.add_entries(de)

        except NoOptionError as error:
            string = "Skipping LocalBox '%s' due to missing option '%s'" % (section, error.option)
            getLogger('main').debug(string)
    print sites
    gui.mainloop()

if __name__ == "__main__":
    main()
