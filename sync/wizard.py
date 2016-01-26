"""
Add Localbox Wizard
"""
from pprint import pprint
from os.path import isdir
from os.path import exists
from os.path import dirname
from os import makedirs
from json import loads
from json import dumps

from Tkinter import Tk
from Tkinter import Label
from Tkinter import Entry
from Tkinter import Button
from Tkinter import END
import tkFileDialog
try:
    from urllib2 import HTTPError
    from urllib2 import URLError
    from httplib import BadStatusLine
except:
    from urllib.error import HTTPError # pylint: disable=F0401,E0611
    from urllib.error import URLError # pylint: disable=F0401,E0611
    from http.client import BadStatusLine

from .localbox import LocalBox
from .auth import Authenticator
from .localbox import AlreadyAuthenticatedError
from .gpg import gpg
from .defaults import SITESINI_PATH


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
        self.button = Button(master=self, text=self.translate("errorbuttontext"), command=self.close)
        self.button.grid(row=1, column=0)

    def close(self):
        self.parent.update()
        self.destroy()

class Wizard(Tk):
    def __init__(self, parent=None, language=None, configparser=None, topwindow=None):
        Tk.__init__(self)
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
        #server

        self.label = Label(master=self, text=self.translate("urltext"))
        self.label.grid(row=0, column=0)
        self.entry = Entry(master=self)
        self.entry.insert(0, "https://localhost:8001/")
        self.entry.grid(row=1, column=0)
        self.label2 = Label(master=self, text=self.translate("labeltext"))
        self.label2.grid(row=2, column=0)
        self.entry2 = Entry(master=self)
        self.entry2.insert(0, "label")
        self.entry2.grid(row=3, column=0)
        self.button = Button(master=self, text=self.translate("buttontext"), command=self.next_1)
        self.button.grid(row=4, column=0)

    def next_1(self):
        server_url = self.entry.get()
        server = self.validate_server(server_url)
        if server != None and self.entry2.get() not in self.configparser.sections():
            self.server_url = server_url
            self.box_label = self.entry2.get()
        else:
            #TODO: Error
            return Errorwindow("Error with input data", parent=self, language=self.translate)
        self.window1()

    def window1(self):
        self.clear()
        #folder
        self.label = Label(master=self, text=self.translate("label2text"))
        self.label.grid(row=0, column=0)
        self.entry = Entry(master=self)
        self.entry.grid(row=1, column=0)
        self.chooser = Button(master=self, text=self.translate("choosertext"), command=self.get_file)
        self.chooser.grid(row=1, column=1)
        self.button = Button(master=self, text=self.translate("button2text"), command=self.next_2)
        self.button.grid(row=2, column=0)

    def next_2(self):
        filepath = self.entry.get()
        if isdir(filepath):
            self.filepath = filepath
        else:
            Errorwindow("Need valid directory", parent=self, language=self.language)
        authenticator = Authenticator(self.localbox.get_authentication_url(), self.box_label)
        self.localbox.add_authenticator(authenticator)
        if authenticator.has_client_credentials():
            self.window3()
        else:
            self.window2()

    def window2(self):
        self.clear()
        # authentication
        self.label = Label(master=self, text=self.translate("label3textusername"))
        self.label.grid(row=0, column=0)
        self.entry = Entry(master=self)
        self.entry.grid(row=1, column=0)
        self.label2 = Label(master=self, text=self.translate("label3textpass"))
        self.label2.grid(row=2, column=0)
        self.password = Entry(master=self, show="*")
        self.password.grid(row=3, column=0)
        self.button = Button(master=self, text=self.translate("button3text"), command=self.next_3)
        self.button.grid(row=4, column=0)

    def next_3(self):
        self.username = self.entry.get()
        password = self.password.get()
        self.localbox.add_authenticator(Authenticator(self.localbox.get_authentication_url(), self.box_label))
        try:
            if self.localbox.authenticator.init_authenticate(self.username, password):
                print "done"
            else:
                print "password error"
                return Errorwindow("Username/Password incorrect", parent=self, language=self.translate)
        except AlreadyAuthenticatedError():
            print "already authenticated"
        self.window3()

    def window3(self):
        response = self.localbox.call_user()
        result = loads(response.read())
        pprint(result)
        if self.username is None:
            self.username = result['user']
        self.clear()
        if result.has_key('private_key') and result.has_key('public_key'):
            self.label = Label(master=self, text=self.translate("give passphrase"))
            self.privkey = result['private_key']
            self.pubkey = result['public_key']
        else:
            self.label = Label(master=self, text=self.translate("new passphrase"))
        self.label.grid(row=0, column=0)
        self.passphrase = Entry(master=self)
        self.passphrase.grid(row=1, column=0)
        self.button = Button(master=self, text=self.translate("passpharsebutton"), command=self.next_4)
        self.button.grid(row=2, column=0)
       

    def next_4(self):
        # set up gpg
        keys = gpg()
        self.passphrasestring = self.passphrase.get()
        if self.pubkey is not None and self.privkey is not None:
            result = keys.add_keypair(self.pubkey, self.privkey, self.box_label, self.username, self.passphrasestring)
            if result is None:
                return Errorwindow("Wrong passphase", parent=self, language=self.translate)
        else:
            fingerprint = keys.generate(self.passphrasestring, self.box_label, self.username)
            data = {'private_key': keys.get_key(fingerprint, True),
                    'public_key': keys.get_key(fingerprint, False) }
            json = dumps(data)
            #register key data
            self.localbox.call_user(json)
        self.save()
        #self.label = Label(master=self, text=self.translate("done"))
        #self.label.grid(row=0, column=0)
        #self.button = Button(master=self, text=self.translate("end_of_wizard_button"), command=self.exit_button)
        #self.button.grid(row=1, column=0)

    def exit_button(self):
        self.topwindow.update()
        self.destroy()

    def get_file(self):
        result = tkFileDialog.askdirectory()
        if len(result) != 0:
            self.entry.delete(0, END)
            self.entry.insert(0, result)


    def validate_server(self, server_url):
        self.localbox = LocalBox(server_url)
        try:
            self.localbox.get_authentication_url()
            print "success"
            return self.localbox
        except (URLError, BadStatusLine, ValueError, AlreadyAuthenticatedError):
            print "failed"
            return None


    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()


    def translate(self, string):
        if self.language == None:
            print "Warning: Translation not loaded"
            return string
        return self.language.lgettext(string)

    def save(self):
        try:
            self.configparser.add_section(self.box_label)
            self.configparser.set(self.box_label, 'url', self.server_url)
            self.configparser.set(self.box_label, 'path', self.filepath)
            self.configparser.set(self.box_label, 'direction', 'sync')
            self.configparser.set(self.box_label, 'passphrase',
                                  self.passphrasestring)
            sitesini = SITESINI_PATH
            if not exists(dirname(SITESINI_PATH)):
                makedirs(dirname(SITESINI_PATH))
            with open(SITESINI_PATH, 'wb') as configfile:
                self.configparser.write(configfile)
            self.clear()
            conflabel = Label(text=self.language.lgettext("config safe success text"), master=self)
            conflabel.grid(row=0, column=0)
            confbutton = Button(master=self, text=self.language.lgettext("closebutton"),
                                command=self.endwizard)
            confbutton.grid(row=1, column=0)
        except ConfigError as error:
            self.clear()
            Label(text=error.message, master=self).grid(row=0, column=0)
            errorbutton = Button(master=self, text=self.language.lgettext("closebutton"),
                                 command=self.endwizard)
            errorbutton.grid(row=1, column=0)

    def endwizard(self):
        self.topwindow.update_window()
        self.destroy()
#Wizard().mainloop()
