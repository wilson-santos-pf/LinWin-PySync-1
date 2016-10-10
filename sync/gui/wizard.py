import json
import wx, wx.wizard, os
from httplib import BadStatusLine
from logging import getLogger
from urllib2 import URLError
from socket import error as SocketError

import errno

import sync.gui.gui_utils as gui_utils
import sync.auth as auth
from sync.controllers.localbox_ctrl import SyncItem
from sync.gpg import gpg
from sync.localbox import LocalBox


class NewSyncWizard(wx.wizard.Wizard):
    def __init__(self, sync_list_ctrl):
        wx.wizard.Wizard.__init__(self, None, -1, _(gui_utils.NEW_SYNC_DIALOG_TITLE))

        # Attributes
        self.localbox_client = None
        self.ctrl = sync_list_ctrl
        self.username = None
        self.path = None
        self.box_label = None

        self.page1 = NewSyncInputsWizardPage(self)
        self.page2 = LoginWizardPage(self)
        self.page3 = PassphraseWizardPage(self)

        wx.wizard.WizardPageSimple.Chain(self.page1, self.page2)
        wx.wizard.WizardPageSimple.Chain(self.page2, self.page3)

        # self.FitToPage(self.page1)
        self.SetPageSize(gui_utils.NEW_SYNC_WIZARD_SIZE)

        self.RunWizard(self.page1)

        self.Destroy()


class NewSyncInputsWizardPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        """Constructor"""
        wx.wizard.WizardPageSimple.__init__(self, parent)

        # Attributes
        self.parent = parent
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._label = wx.TextCtrl(self)
        self._url = wx.TextCtrl(self)
        self._selected_dir = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.btn_select_dir = wx.Button(self, label=_('Select'), size=(95, 30))

        # Layout
        self._DoLayout()

        self.Bind(wx.EVT_BUTTON, self.select_localbox_dir, self.btn_select_dir)
        self.Bind(wx.wizard.EVT_WIZARD_BEFORE_PAGE_CHANGED, self.is_authenticated)
        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.validate_new_sync_inputs)

    def is_authenticated(self, event):

        if event.GetDirection():
            # going forwards
            if self.parent.localbox_client and auth.is_authenticated(self.parent.localbox_client, self.label):
                getLogger(__name__).debug('Checking if is already authenticated for: %s' % self.label)
                wx.wizard.WizardPageSimple.Chain(self.parent.page1, self.parent.page3)

    def _DoLayout(self):
        sizer = wx.FlexGridSizer(3, 3, 10, 10)

        sizer.Add(wx.StaticText(self, label=_("Label:")),
                  1, wx.ALIGN_RIGHT)
        sizer.Add(self._label, 0, wx.EXPAND)
        sizer.AddGrowableCol(1)
        sizer.Add(wx.StaticText(self.parent, label=''))

        sizer.Add(wx.StaticText(self, label=_("URL:")),
                  0, wx.ALIGN_RIGHT)
        sizer.Add(self._url, 0, wx.EXPAND)
        sizer.Add(wx.StaticText(self, label=''))

        sizer.Add(wx.StaticText(self, label=_("Path:")),
                  0, wx.ALIGN_RIGHT)
        sizer.Add(self._selected_dir, 0, wx.EXPAND)
        sizer.Add(self.btn_select_dir, 0, wx.EXPAND)

        self._sizer.Add(sizer, 1, wx.ALL | wx.EXPAND, border=10)

        self.SetSizer(self._sizer)

    def select_localbox_dir(self, event):
        dialog = wx.DirDialog(None, _("Choose a file"), style=wx.DD_DEFAULT_STYLE, defaultPath=os.getcwd(),
                              pos=(10, 10))
        if dialog.ShowModal() == wx.ID_OK:
            self._selected_dir.SetValue(dialog.GetPath())

        dialog.Destroy()

    def validate_new_sync_inputs(self, event):
        getLogger(__name__).debug('nextPage: %s' % self.GetNext())
        # step 1
        label = self.label
        url = self.url
        path = self.path

        if gui_utils.is_valid_input(label) and gui_utils.is_valid_input(url) and gui_utils.is_valid_input(path):
            self.sync_item = SyncItem(label=label,
                                      url=url,
                                      path=path)

            try:
                self.parent.localbox_client = LocalBox(url, label)
            except (URLError, BadStatusLine, ValueError,
                    auth.AlreadyAuthenticatedError) as error:
                getLogger(__name__).debug("error with authentication url thingie")
                getLogger(__name__).exception(error)
            except SocketError as e:
                if e.errno != errno.ECONNRESET:
                    raise  # Not error we are looking for
                getLogger(__name__).error('Failed to connect to server, maybe forgot https? %s', e)

            self.parent.box_label = label
            self.parent.path = path

            if not self.parent.localbox_client:
                getLogger(__name__).error('%s is not a valid URL' % url)
                gui_utils.show_error_dialog(message=_('%s is not a valid URL') % url, title=_('Invalid URL'))
                event.Veto()

        else:
            event.Veto()

    @property
    def path(self):
        return self._selected_dir.GetValue()

    @property
    def label(self):
        return self._label.GetValue().encode()

    @property
    def url(self):
        return self._url.GetValue().encode()


class LoginWizardPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)

        # Attributes
        self.parent = parent
        self.is_authenticated = False
        self._username = wx.TextCtrl(self)
        self._password = wx.TextCtrl(self, style=wx.TE_PASSWORD)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer = main_sizer

        input_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer.Add(wx.StaticText(self, label=_("Username:")),
                        0, wx.ALL | wx.ALIGN_LEFT)
        input_sizer.Add(self._username, 0, wx.ALL | wx.EXPAND)
        input_sizer.Add(wx.StaticText(self, label=_("Password:")),
                        0, wx.ALL | wx.ALIGN_LEFT, border=gui_utils.DEFAULT_BORDER)
        input_sizer.Add(self._password, 0, wx.ALL | wx.EXPAND)

        main_sizer.Add(input_sizer, 1, wx.ALL | wx.EXPAND, border=gui_utils.DEFAULT_BORDER)

        self.already_authenticated_sizer = wx.BoxSizer(wx.VERTICAL)
        self._label_already_authenticated = wx.StaticText(self, label='')
        self.already_authenticated_sizer.Add(self._label_already_authenticated, 1, wx.ALL | wx.EXPAND,
                                             border=gui_utils.DEFAULT_BORDER)

        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.call_password_authentication)
        self.Bind(wx.wizard.EVT_WIZARD_BEFORE_PAGE_CHANGED, self.should_login)

    def should_login(self, event):

        if self.parent.localbox_client.authenticator.is_authenticated():
            self.is_authenticated = True
            self._label_already_authenticated.SetLabel(
                _("Already authenticated for: %s. Skipping authentication with password." % self.parent.box_label))
            self.SetSizer(self.already_authenticated_sizer)
            self.already_authenticated_sizer.ShowItems(show=True)
            self.main_sizer.ShowItems(show=False)
        else:
            self.is_authenticated = False
            self.already_authenticated_sizer.ShowItems(show=False)
            self.main_sizer.ShowItems(show=True)
            self.SetSizer(self.main_sizer)

        self.Layout()

    def call_password_authentication(self, event):
        getLogger(__name__).debug("authenticating... - direction: %s", event.GetDirection())

        if event.GetDirection():
            # going forwards
            if not self.is_authenticated:
                if gui_utils.is_valid_input(self.username) and gui_utils.is_valid_input(self.password):
                    try:
                        success = self.parent.localbox_client.authenticator.authenticate_with_password(
                            self.username,
                            self.password)
                        is_exception = False
                    except Exception as error:
                        success = False
                        is_exception = True
                        getLogger(__name__).error('Problem authenticating with password: %s' % error)

                    if not success:
                        if not is_exception:
                            title = _('Error')
                            error_msg = _("Username/Password incorrect")
                        else:
                            title = _('Invalid credentials')
                            error_msg = _(
                                "Authentication problem. Please check the logs and send them to the develop team.")

                        gui_utils.show_error_dialog(message=error_msg, title=title)
                        event.Veto()
                else:
                    event.Veto()

    @property
    def username(self):
        return self._username.GetValue()

    @property
    def password(self):
        return self._password.GetValue()


class PassphraseWizardPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)

        # Attributes
        self.parent = parent
        self.pubkey = None
        self.privkey = None
        self._label = wx.StaticText(self, label='')
        self._entry_passphrase = wx.TextCtrl(self, style=wx.TE_PASSWORD)

        # Layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        input_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer.Add(self._label, 0, flag=wx.EXPAND | wx.ALL)
        input_sizer.Add(self._entry_passphrase, 0, flag=wx.EXPAND | wx.ALL)

        main_sizer.Add(input_sizer, 1, flag=wx.EXPAND | wx.ALL, border=gui_utils.DEFAULT_BORDER)

        self.SetSizer(main_sizer)
        self.Layout()

        self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.store_keys)
        self.Bind(wx.wizard.EVT_WIZARD_BEFORE_PAGE_CHANGED, self.setup_passphrase_panel)

    @property
    def passphrase(self):
        return self._entry_passphrase.GetValue()

    def setup_passphrase_panel(self, event):
        # step #3

        if event.GetDirection():
            # TODO: handle call_user error with dialog
            # eg: [filesystem] bindpoint -> with non existing folder gives error
            response = self.parent.localbox_client.call_user()
            result = json.loads(response.read())

            if self.parent.username is None:
                getLogger(__name__).debug("username is None")
                self.parent.username = result['user']

            if 'private_key' in result and 'public_key' in result:
                getLogger(__name__).debug("private key and public key found")
                label = _('Give Passphrase')
                self.privkey = result['private_key']
                self.pubkey = result['public_key']
            else:
                getLogger(__name__).debug("private key or public key not found")
                getLogger(__name__).debug(str(result))
                label = _("New Passphrase")

            self._label.SetLabel(label)

    def store_keys(self, event):
        if event.GetDirection():
            if gui_utils.is_valid_input(self.passphrase):
                # going forward
                # step #4
                getLogger(__name__).debug("wizard next_4")
                # set up gpg
                keys = gpg()
                if self.pubkey is not None and self.privkey is not None:
                    getLogger(__name__).debug("private key found and public key found")

                    result = keys.add_keypair(self.pubkey, self.privkey,
                                              self.parent.box_label, self.parent.username,
                                              self.passphrase)
                    if result is None:
                        getLogger(__name__).debug("could not add keypair")
                        return gui_utils.show_error_dialog(message=_('Wrong passphase'), title=_('Error'))
                else:
                    getLogger(__name__).debug("public keys not found. generating...")
                    fingerprint = keys.generate(self.passphrase,
                                                self.parent.box_label, self.parent.username)
                    data = {'private_key': keys.get_key(fingerprint, True),
                            'public_key': keys.get_key(fingerprint, False)}
                    data_json = json.dumps(data)
                    # register key data
                    self.parent.localbox_client.call_user(data_json)

                self.add_new_sync_item()
            else:
                event.Veto()

    def add_new_sync_item(self):
        item = SyncItem(url=self.parent.localbox_client.url,
                        label=self.parent.box_label,
                        direction='sync',
                        path=self.parent.path,
                        user=self.parent.username,
                        passphrase=self.passphrase)
        self.parent.ctrl.add(item)
        self.parent.ctrl.save()
        getLogger(__name__).debug("new sync saved")
