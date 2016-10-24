import os
import subprocess
import sys
from logging import getLogger
from gettext import gettext as _

from desktop_utils.controllers import openfiles_ctrl
from loxcommon import os_utils
from sync import defaults
from sync.controllers.localbox_ctrl import ctrl as sync_ctrl
from sync.controllers.login_ctrl import LoginController
from sync.gui import gui_utils
from sync.gui.gui_wx import PassphraseDialog
from sync.localbox import LocalBox
from version import VERSION

FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_NORMAL = 0x80


def open_file_ext(url):
    if sys.platform == 'win32':
        p = os.startfile(url)
    elif sys.platform == 'darwin':
        p = subprocess.Popen(['open', url])
    else:
        try:
            p = subprocess.Popen(['xdg-open', url])
            p.communicate()
        except OSError as ex:
            getLogger(__name__).exception('Unable to open %s' % url, ex)


def change_file_attribute(filename, attr_flag):
    if sys.platform == 'win32':
        import ctypes
        try:
            eval('unicode(filename)')
            u_filename = unicode(filename)
        except SyntaxError:
            u_filename = str(filename)

        ret = ctypes.windll.kernel32.SetFileAttributesW(u_filename, attr_flag)
        if not ret:
            getLogger(__name__).error('cannot change file %s attributes to %s' % (tmp_decoded_filename, attr_flag))


def hide_file(filename):
    change_file_attribute(filename, FILE_ATTRIBUTE_HIDDEN)


def unhide_file(filename):
    change_file_attribute(filename, FILE_ATTRIBUTE_NORMAL)


try:
    if __name__ == '__main__':
        getLogger(__name__).info("LocalBox Desktop Utils Version: %s", VERSION)

        if len(sys.argv) < 2:
            getLogger(__name__).error("No file supplied")
        else:
            filename = ' '.join(sys.argv[1:])
            getLogger(__name__).info("File: %s" % filename)

            # verify if the file belongs to any of the configured syncs
            sync_list = sync_ctrl.list

            cur_sync_item = None
            localbox_client = None
            localbox_filename = None
            for sync_item in sync_list:
                getLogger(__name__).debug('sync path: %s' % sync_item.path)
                if filename.startswith(sync_item.path):
                    found = True
                    cur_sync_item = sync_item
                    localbox_filename = os_utils.remove_extension(filename.replace(sync_item.path, ''),
                                                                  defaults.LOCALBOX_EXTENSION)
                    localbox_client = LocalBox(sync_item.url, sync_item.label)
                    break

            if not localbox_client or not localbox_filename:
                gui_utils.show_error_dialog(_('%s does not belong to any localbox') % filename, 'Error', True)
                getLogger(__name__).error('%s does not belong to any localbox' % filename)
                exit(1)

            # get passphrase
            label = localbox_client.authenticator.label
            passphrase = LoginController().get_passphrase(label, remote=True)
            if not passphrase:
                gui_utils.ask_passphrase(localbox_client, PassphraseDialog)
                passphrase = LoginController().get_passphrase(label, remote=False)
                if not passphrase:
                    gui_utils.show_error_dialog(_('Failed to get passphrase for label: %s.') % label, 'Error', True)
                    getLogger(__name__).error('failed to get passphrase for label: %s. Exiting..' % label)
                    exit(1)

            # decode file
            decoded_contents = localbox_client.decode_file(localbox_filename, filename, passphrase)
            if decoded_contents is not None:
                # write file
                tmp_decoded_filename = os_utils.remove_extension(filename, defaults.LOCALBOX_EXTENSION)
                getLogger(__name__).info('tmp_decoded_filename: %s' % tmp_decoded_filename)

                if os.path.exists(tmp_decoded_filename):
                    os.remove(tmp_decoded_filename)

                localfile = open(tmp_decoded_filename, 'wb')
                localfile.write(decoded_contents)
                localfile.close()

                # hide file
                hide_file(tmp_decoded_filename)

                # open file
                open_file_ext(tmp_decoded_filename)

                openfiles_ctrl.add(tmp_decoded_filename)
            else:
                gui_utils.show_error_dialog(_('Failed to decode contents'), 'Error', True)
                getLogger(__name__).info('failed to decode contents. aborting')

except Exception as ex:
    getLogger(__name__).exception(ex)
