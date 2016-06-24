"""
Add LocalBox Wizard
"""
from logging import getLogger
from os.path import isdir
from os.path import exists
from os.path import dirname
from os import makedirs
from base64 import b64decode
from json import loads
from json import dumps

from Tkinter import Tk
from Tkinter import Label
from Tkinter import Entry
from Tkinter import Button
from Tkinter import END
import tkFileDialog
try:
    from urllib2 import URLError
    from urllib2 import HTTPError
    from httplib import BadStatusLine
except ImportError:
    from urllib.error import URLError  # pylint: disable=F0401,E0611
    from urllib.error import HTTPError  # pylint: disable=F0401,E0611
    from http.client import BadStatusLine  # pylint: disable=F0401,E0611

from .localbox import LocalBox
from .auth import Authenticator
from .localbox import AlreadyAuthenticatedError
from .gpg import gpg
from .defaults import SITESINI_PATH
from .syncer import Syncer


class ConfigError(Exception):
    pass


class Errorwindow(Tk):

    def __init__(self, message, parent=None, language=None):
        Tk.__init__(self)
        self.parent = parent
        self.translate = language
        self.title = self.translate("Error")
        self.label = Label(master=self, text=self.translate(message))
        self.label.grid(row=0, column=0)
        self.button = Button(master=self,
                             text=self.translate("errorbuttontext"),
                             command=self.close)
        self.button.grid(row=1, column=0)

    def close(self):
        self.parent.update()
        self.destroy()


class Wizard(Tk):

    def __init__(self, parent=None, language=None, configparser=None,
                 topwindow=None, siteslist=None):
        Tk.__init__(self)
        if siteslist is None:
            self.siteslist = []
        else:
            self.sites = siteslist
        getLogger(__name__).debug("initializing wizard")
        self.parent = parent
        self.language = language
        self.topwindow = topwindow
        self.title = self.translate("wizardtitle")
        self.username = None
        self.privkey = None
        self.pubkey = None
        self.configparser = configparser
        self.passphrase = None
        self.password = None
        self.filepath = None
        self.localbox = None
        self.box_label = None
        self.chooser = None
        self.server_url = None
        self.eventwindow = None
        self.passphrasestring = None
        # server

        self.label = Label(master=self, text=self.translate("urltext"))
        self.label.grid(row=0, column=0)
        self.entry = Entry(master=self, width=30)
        self.entry.insert(0, "https://localhost:8001/")
        self.entry.grid(row=1, column=0)
        self.label2 = Label(master=self, text=self.translate("labeltext"))
        self.label2.grid(row=2, column=0)
        self.entry2 = Entry(master=self, width=30)
        self.entry2.insert(0, "label")
        self.entry2.grid(row=3, column=0)
        self.button = Button(master=self, text=self.translate("buttontext"),
                             command=self.next_1)
        self.button.grid(row=4, column=0)
        getLogger(__name__).debug("wizard initialized")

    def next_1(self):
        getLogger(__name__).debug("wizard next_1")
        server_url = self.entry.get()
        server = self.validate_server(server_url)
        if server is not None and self.entry2.get() not in \
           self.configparser.sections():
            getLogger(__name__).debug(
                "server is not not and entry not in sections = true")
            self.server_url = server_url
            self.box_label = self.entry2.get()
        else:
            getLogger(__name__).debug(
                "server is not not and entry not in sections = false")
            return Errorwindow("Error with input data", parent=self,
                               language=self.translate)
        self.window1()

    def window1(self):
        getLogger(__name__).debug("wizard window_1")
        self.clear()
        # folder
        self.label = Label(master=self, text=self.translate("label2text"))
        self.label.grid(row=0, column=0)
        self.entry = Entry(master=self, width=30)
        self.entry.grid(row=1, column=0)
        self.chooser = Button(master=self, text=self.translate("choosertext"),
                              command=self.get_file)
        self.chooser.grid(row=1, column=1)
        self.button = Button(master=self, text=self.translate("button2text"),
                             command=self.next_2)
        self.button.grid(row=2, column=0)

    def next_2(self):
        getLogger(__name__).debug("wizard next_2")
        filepath = self.entry.get()
        if isdir(filepath):
            getLogger(__name__).debug("isdir filepath = true")
            self.filepath = filepath
        else:
            getLogger(__name__).debug("isdir filepath = false")
            Errorwindow("Need valid directory", parent=self,
                        language=self.language)
        authenticator = Authenticator(self.localbox.get_authentication_url(),
                                      self.box_label)
        try:
            self.localbox.add_authenticator(authenticator)
            if authenticator.has_client_credentials():
                getLogger(__name__).debug("has_client_credentials = false")
                self.window3()
            else:
                getLogger(__name__).debug("has_client_credentials = true")
                self.window2()
        except AlreadyAuthenticatedError():
            self.window3()

    def window2(self):
        getLogger(__name__).debug("wizard window2")
        self.clear()
        # authentication
        self.label = Label(master=self,
                           text=self.translate("label3textusername"))
        self.label.grid(row=0, column=0)
        self.entry = Entry(master=self, width=30)
        self.entry.grid(row=1, column=0)
        self.label2 = Label(master=self, text=self.translate("label3textpass"))
        self.label2.grid(row=2, column=0)
        self.password = Entry(master=self, show="*", width=30)
        self.password.grid(row=3, column=0)
        self.button = Button(master=self, text=self.translate("button3text"),
                             command=self.next_3)
        self.button.grid(row=4, column=0)

    def next_3(self):
        getLogger(__name__).debug("wizard next_3")
        self.username = self.entry.get()
        password = self.password.get()
        authurl = self.localbox.get_authentication_url()
        self.localbox.add_authenticator(Authenticator(authurl, self.box_label))
        try:
            if self.localbox.authenticator.init_authenticate(self.username,
                                                             password):
                getLogger(__name__).debug("ini authenticate = true")
                print("done")
            else:
                getLogger(__name__).debug("ini authenticate = false")
                print("password error")
                return Errorwindow("Username/Password incorrect", parent=self,
                                   language=self.translate)
        except AlreadyAuthenticatedError as error:
            getLogger(__name__).debug(
                "ini authenticate = AlreadyAuthenticatedError")
            getLogger(__name__).exception(error)
            print("already authenticated")
            Errorwindow("Already authenticated. Please send localbox-sync.log to show us how you did this. You might want to clear the AppData folder as well",
                        language=self.translate, parent=self)
        except (HTTPError, URLError) as error:
            getLogger(__name__).debug(
                "Problem connecting to the authentication server")
            getLogger(__name__).exception(error)
            Errorwindow("Authentication Problem: " + error.message,
                        language=self.translate, parent=self)
        getLogger(__name__).debug("launching window3")
        self.window3()

    def window3(self):
        getLogger(__name__).debug("wizard window3")
        response = self.localbox.call_user()
        result = loads(response.read())
        print result
        if self.username is None:
            getLogger(__name__).debug("username is None")
            self.username = result['user']
        self.clear()
        if 'private_key' in result and 'public_key' in result:
            getLogger(__name__).debug("private key and public key found")
            self.label = Label(master=self,
                               text=self.translate("give passphrase"))
            self.privkey = result['private_key']
            self.pubkey = result['public_key']
        else:
            getLogger(__name__).debug("private key or public key not found")
            getLogger(__name__).debug(str(result))
            self.label = Label(master=self,
                               text=self.translate("new passphrase"))
        self.label.grid(row=0, column=0)
        self.passphrase = Entry(master=self, show="*", width=30)
        self.passphrase.grid(row=1, column=0)
        self.button = Button(master=self,
                             text=self.translate("passpharsebutton"),
                             command=self.next_4)
        self.button.grid(row=2, column=0)

    def next_4(self):
        getLogger(__name__).debug("wizard next_4")
        # set up gpg
        keys = gpg()
        self.passphrasestring = self.passphrase.get()
        if self.pubkey is not None and self.privkey is not None:
            getLogger(__name__).debug("private key found and public key found")

            result = keys.add_keypair(self.pubkey, self.privkey,
                                      self.box_label, self.username,
                                      self.passphrasestring)
            if result is None:
                getLogger(__name__).debug("could not add keypair")
                return Errorwindow("Wrong passphase", parent=self,
                                   language=self.translate)
        else:
            getLogger(__name__).debug("public keys not found")
            fingerprint = keys.generate(self.passphrasestring,
                                        self.box_label, self.username)
            data = {'private_key': keys.get_key(fingerprint, True),
                    'public_key': keys.get_key(fingerprint, False)}
            json = dumps(data)
            # register key data
            self.localbox.call_user(json)
        self.save()

    def exit_button(self):
        getLogger(__name__).debug("wizard exit_button")
        self.topwindow.update()
        self.destroy()

    def get_file(self):
        getLogger(__name__).debug("wizard get_file")
        result = tkFileDialog.askdirectory()
        if len(result) != 0:
            self.entry.delete(0, END)
            self.entry.insert(0, result)

    def validate_server(self, server_url):
        getLogger(__name__).debug("wizard validate_server")
        self.localbox = LocalBox(server_url)
        try:
            self.localbox.get_authentication_url()
            print("success")
            return self.localbox
        except (URLError, BadStatusLine, ValueError,
                AlreadyAuthenticatedError) as error:
            getLogger(__name__).debug("error with uthentication url thingie")
            getLogger(__name__).exception(error)
            print("failed")
            return None

    def clear(self):
        getLogger(__name__).debug("wizard clear")
        for widget in self.winfo_children():
            widget.destroy()

    def translate(self, string):
        getLogger(__name__).debug("wizard translate")
        if self.language is None:
            getLogger(__name__).debug("language is none")
            print("Warning: Translation not loaded")
            return string
        return self.language.lgettext(string)

    def save(self):
        getLogger(__name__).debug("wizard save")
        try:
            self.configparser.add_section(self.box_label)
            self.configparser.set(self.box_label, 'url', self.server_url)
            self.configparser.set(self.box_label, 'path', self.filepath)
            self.configparser.set(self.box_label, 'direction', 'sync')
            self.configparser.set(self.box_label, 'passphrase',
                                  self.passphrasestring)
            self.configparser.set(self.box_label, 'user', self.username)

            if not exists(dirname(SITESINI_PATH)):
                getLogger(__name__).debug("not exists dirname sitesini")
                makedirs(dirname(SITESINI_PATH))
            with open(SITESINI_PATH, 'wb') as configfile:
                self.configparser.write(configfile)
            self.clear()
            sll = self.language.lgettext
            conflabel = Label(text=sll("config safe success"), master=self)
            conflabel.grid(row=0, column=0)
            confbutton = Button(master=self, text=sll("closebutton"),
                                command=self.endwizard)
            confbutton.grid(row=1, column=0)
        except ConfigError as error:
            getLogger(__name__).debug("configerror")
            getLogger(__name__).exception(error)
            self.clear()
            Label(text=error.message, master=self).grid(row=0, column=0)
            errorbutton = Button(master=self,
                                 text=self.language.lgettext("closebutton"),
                                 command=self.endwizard)
            errorbutton.grid(row=1, column=0)

    def endwizard(self):
        getLogger(__name__).debug("wizard endwizard")
        self.topwindow.update_window()
        self.destroy()
        self.sites.append(Syncer(self.localbox, self.filepath, 'sync'))
