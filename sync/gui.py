from Tkinter import Tk
from Tkinter import Frame
from Tkinter import Label
from Tkinter import Entry
from Tkinter import Button

from tkMessageBox import showerror
import tkFileDialog

from codecs import open as codecsopen

from Tkinter import END
from ConfigParser import ConfigParser
from ConfigParser import NoOptionError
from os.path import isdir
from os.path import exists
from os.path import dirname
from os import makedirs
from logging import getLogger
from gettext import translation

from .__main__ import prepare_logging
from .auth import Authenticator
from .auth import AuthenticationError
from .database import database_execute
from .defaults import SITESINI_PATH
from .localbox import LocalBox
from .defaults import LOCALE_PATH
from .wizard import Wizard
from .wizard import ConfigError


class UsernameAndPasswordAsker(Tk):
    """
    Window which ask the user for an username and password which checks the
    valitity of said credentials
    """

    def __init__(self, authenticator, translator, parent=None):
        Tk.__init__(self, parent)
        self.title(translator.translate("Authentication Data"))
        self.authenticator = authenticator

        Label(self, text=translator.translate("username")).grid(row=0,
                                                                column=0)
        self.username = Entry(self, width=30)
        self.username.grid(row=0, column=1)
        Label(self, text=translator.translate("password")).grid(row=1,
                                                                column=0)
        self.password = Entry(self, show="*", width=30)
        self.password.grid(row=1, column=1)
        self.button = Button(master=self, text=translator.translate("OK"),
                             command=self.stop_window)
        self.button.grid(row=2)

    def stop_window(self):
        """
        checks authentication and loses the window is authentication is
        succesful. Shows an error when it is not.
        """
        if self.authenticator.init_authenticate(self.username.get(),
                                                self.password.get()):
            self.lock.set()
            self.destroy()
        else:
            showerror(
                'Authentication Failed', 'Could not authenticate, Check username and password')

    def __call__(self):
        self.mainloop()


class Gui(Tk):
    """
    localbox configuration user interface. Tool to make changes in the
    configuration of the localbox.
    """

    def __init__(self, parent=None, configparser=None, siteslist=None):
        Tk.__init__(self, parent)
        if siteslist is None:
            self.siteslist = []
        else:
            self.siteslist = siteslist
        # TODO: more languages stuff
        self.language = translation('localboxsync', localedir=LOCALE_PATH,
                                    languages=['nl'], fallback=True)
        self.configs = []
        self.configparser = configparser
        self.lift()
        self.button = None
        self.update_window()

    def localbox_button(self):
        """
        add an "add localbox" button
        """
        self.button = Button(text=self.language.lgettext("add localbox"),
                             command=self.add_new)
        self.button.grid(row=0, column=0)

    def add_entries(self, dataentryframe):
        """
        add a 'dataentryframe' to the gui in which certain strings are set.
        """
        self.configs.append(dataentryframe)
        position = len(self.configs)
        dataentryframe.grid(row=position, column=0)

    def add_new(self):
        """
        start the wizard to add a new localbox instance.
        """
        wizard = Wizard(
            None, self.language, self.configparser, self, siteslist=self.siteslist)
        wizard.mainloop()

    def update_window(self):
        """
        redraw the window
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.localbox_button()
        location = SITESINI_PATH
        self.configparser.read(location)
        sites = []
        for section in self.configparser.sections():
            try:
                dictionary = {'name': section.encode('ascii', 'replace'),
                              'url': self.configparser.get(section, 'url').encode('ascii', 'replace'),
                              'path': self.configparser.get(section, 'path').encode('ascii', 'replace')}
                sites.append(dictionary)
                passphrase = self.configparser.get(section, 'passphrase').encode('ascii', 'replace')
                dataentry = DataEntry(self, section, dictionary['url'],
                                      dictionary['path'],
                                      self.configparser, passphrase=passphrase,
                                      language=self.language)
                self.add_entries(dataentry)

            except NoOptionError as error:
                getLogger(__name__).exception(error)
                string = "Skipping LocalBox '%s' due to missing option '%s'" %\
                         (section, error.option)
                getLogger(__name__).debug(string)


def get_entry_fields(parent, text, value, row, show=None):
    """
    create a line in the gui consisting of a label with 'text' and a textentry
    with 'value'
    """
    label = Label(text=text, master=parent, justify="left")
    label.grid(column=0, row=row)
    if show is not None:
        entry = Entry(master=parent, show=show, width=30)
    else:
        entry = Entry(master=parent, width=30)
    entry.insert(0, value)
    entry.grid(column=1, row=row)
    return entry


class DataEntry(Frame):
    """
    configuration ui for a single, configured localbox instance.
    """

    def getfile(self):
        """
        open a directory picker and return the directory
        """
        result = tkFileDialog.askdirectory()
        self.local_path.delete(0, END)
        self.local_path.insert(0, result)

    def __init__(self, master=None, name=None, url=None, localdir=None,
                 config=None, passphrase=None, language=None):
        Frame.__init__(self, master=master, relief="raised", borderwidth=2)
        self.master = master
        self.eventwindow = None
        self.configparser = config
        self.orig_name = name
        self.language = language
        mllgt = master.language.lgettext
        self.site_name = get_entry_fields(self, mllgt("name box"), name, 0)
        self.localbox_url = get_entry_fields(self, mllgt("localbox url"), url,
                                             1)
        self.local_path = get_entry_fields(self, mllgt("local path"),
                                           localdir, 2)
        self.passphrase = get_entry_fields(self, mllgt("passphrase"),
                                           passphrase, 3, show="*")
        self.lpbutton = Button(master=self, text=mllgt("folder select"),
                               command=self.getfile)
        self.lpbutton.grid(column=2, row=2)

        self.savebutton = Button(master=self, text=mllgt("save"),
                                 command=self.save)
        self.savebutton.grid(row=5, column=2)
        self.authbutton = Button(master=self, text=mllgt("delete"),
                                 command=self.delete)
        self.authbutton.grid(row=5, column=1)

    def delete(self):
        """
        removes the configuration of this localbox from the config file.
        """
        self.configparser.remove_section(self.orig_name.encode('ascii', 'replace'))
        if not exists(dirname(SITESINI_PATH)):
            makedirs(dirname(SITESINI_PATH))
        with open(SITESINI_PATH, 'wb+') as configfile:
            self.configparser.write(configfile)
        self.master.update_window()

    def save(self):
        """
        saves the configuration of this localbox from the config file.
        """
        try:
            if self.site_name.get() != self.orig_name:
                if (self.configparser.sections() is not None and
                        self.site_name.get() in self.configparser.sections()):
                    raise ConfigError("There is already a site with that name")
            if not isdir(self.local_path.get()):
                raise ConfigError("Share path needs to be a directory")
            if self.site_name.get() != self.orig_name:
                self.configparser.remove_section(self.orig_name)
                self.configparser.add_section(self.site_name.get())
                if self.orig_name in self.configparser.sections():
                    sql = "update sites set site=? where site=?;"
                    database_execute(sql, (self.site_name.get(),
                                           self.orig_name))
                self.orig_name = self.site_name.get()

            self.configparser.set(self.site_name.get(), 'url',
                                  self.localbox_url.get())
            self.configparser.set(self.site_name.get(), 'path',
                                  self.local_path.get())
            self.configparser.set(self.site_name.get(), 'passphrase',
                                  self.passphrase.get())
            if not exists(dirname(SITESINI_PATH)):
                makedirs(dirname(SITESINI_PATH))
            with open(SITESINI_PATH, 'wb+') as configfile:
                self.configparser.write(configfile)
            self.eventwindow = Tk()
            smll = self.master.language.lgettext
            self.eventwindow.title(smll("successwindowtitle"))
            conflabel = Label(text=smll("config safe success text"),
                              master=self.eventwindow)
            conflabel.grid(row=0, column=0)
            confbutton = Button(master=self.eventwindow,
                                text=smll("closebutton"),
                                command=self.close_exception_window)
            confbutton.grid(row=1, column=0)
        except ConfigError as error:
            getLogger(__name__).exception(error)
            self.eventwindow = Tk()
            self.eventwindow.title(smll("error"))
            Label(text=error.message, master=self.eventwindow).grid(row=0,
                                                                    column=0)
            errorbutton = Button(master=self.eventwindow, text=smll("close"),
                                 command=self.close_exception_window)
            errorbutton.grid(row=1, column=0)

    def close_exception_window(self):
        """
        closes the event window (which mentions configuration errors)
        """
        self.eventwindow.destroy()

    def authenticate(self):
        """
        tries to authenticate to the configured box with the authentication data supplied.
        """
        localbox = LocalBox(self.localbox_url.get())
        authurl = localbox.get_authentication_url()
        authenticator = Authenticator(authurl, self.site_name.get())
        if not authenticator.has_client_credentials():
            credentials = UsernameAndPasswordAsker(authenticator,
                                                   self.language)
            credentials.__call__()
            credentials.lock.wait()
            # Show username/password field
            if authenticator.init_authenticate(credentials.username.get(),
                                               credentials.password.get()):
                getLogger(__name__).info("succes")
            else:
                getLogger(__name__).info("failure")
        else:
            try:
                authenticator.authenticate_with_client_secret()
                getLogger(__name__).info("credentials seem valid")
            except AuthenticationError as error:
                getLogger(__name__).exception(error)
                getLogger(__name__).info("your credentials are invalid")


def main(gui=None, sites=None):
    """
    starts the gui component of localbox
    """
    getLogger(__name__).debug("Gui Main Started")
    location = SITESINI_PATH
    configparser = ConfigParser()
    configparser.read(location)
    if gui is None:
        getLogger(__name__).debug("Started a new gui")
        gui = Gui(configparser=configparser, siteslist=sites)

    getLogger(__name__).debug("While loop start")
    if sites is None:
        sites = []
    gui.title(gui.language.lgettext('settingstitle'))
    getLogger(__name__).debug("Launching GUI main loop")
    gui.mainloop()
    getLogger(__name__).debug("done with GUI mainloop")

if __name__ == "__main__":
    prepare_logging()
    main()
