"""
main module for localbox sync
"""
import os
from logging import getLogger
from os import makedirs
from os.path import dirname
from os.path import isdir
from sys import argv
from threading import Event

from loxcommon import os_utils
from loxcommon.os_utils import open_file_ext, hide_file
from sync import defaults
from sync.controllers import openfiles_ctrl
from sync.controllers.localbox_ctrl import ctrl as sync_ctrl
from sync.controllers.login_ctrl import LoginController
from sync.gui import gui_utils
from sync.gui import gui_wx
from sync.gui.gui_wx import PassphraseDialog
from sync.gui.taskbar import taskbarmain
from sync.localbox import LocalBox
from sync.syncer import MainSyncer
from .defaults import LOG_PATH

try:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError
    from ConfigParser import NoSectionError
    from urllib2 import URLError
except ImportError:
    from configparser import ConfigParser  # pylint: disable=F0401,W0611
    from configparser import NoOptionError  # pylint: disable=F0401,W0611
    from configparser import NoSectionError  # pylint: disable=F0401,W0611
    from urllib.error import URLError  # pylint: disable=F0401,W0611,E0611

    raw_input = input  # pylint: disable=W0622,C0103


def run_sync_daemon():
    try:
        EVENT = Event()
        EVENT.clear()

        MAIN = MainSyncer(EVENT)
        MAIN.start()

        taskbarmain(MAIN)
    except Exception as error:  # pylint: disable=W0703
        getLogger(__name__).exception(error)


def run_file_decryption(filename):
    try:
        getLogger(__name__).info('Decrypting and opening file: %s', filename)

        # verify if the file belongs to any of the configured syncs
        sync_list = sync_ctrl.list

        localbox_client = None
        localbox_filename = None
        for sync_item in sync_list:
            getLogger(__name__).debug('sync path: %s' % sync_item.path)
            sync_path = sync_item.path if sync_item.path.endswith('/') else sync_item.path + os.path.sep
            if filename.startswith(sync_path):
                localbox_filename = os_utils.remove_extension(filename.replace(sync_item.path, ''),
                                                              defaults.LOCALBOX_EXTENSION)
                localbox_client = LocalBox(sync_item.url, sync_item.label)
                break

        if not localbox_client or not localbox_filename:
            gui_utils.show_error_dialog(_('%s does not belong to any configured localbox') % filename, 'Error',
                                        True)
            getLogger(__name__).error('%s does not belong to any configured localbox' % filename)
            exit(1)

        # get passphrase
        label = localbox_client.authenticator.label
        passphrase = LoginController().get_passphrase(label, remote=True)
        if not passphrase:
            gui_wx.ask_passphrase(localbox_client.username, label)
            passphrase = LoginController().get_passphrase(label, remote=False)
            if not passphrase:
                gui_utils.show_error_dialog(_('Failed to get passphrase for label: %s.') % label, 'Error', True)
                getLogger(__name__).error('failed to get passphrase for label: %s. Exiting..' % label)
                exit(1)

        # decode file
        try:
            decoded_contents = localbox_client.decode_file(localbox_filename, filename, passphrase)
        except URLError:
            gui_utils.show_error_dialog(_('Failed to decode contents'), 'Error', standalone=True)
            getLogger(__name__).info('failed to decode contents. aborting')
            return 1

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

        getLogger(__name__).info('Finished decrypting and opening file: %s', filename)


    except Exception as ex:
        getLogger(__name__).exception(ex)


if __name__ == '__main__':
    if not isdir(dirname(LOG_PATH)):
        makedirs(dirname(LOG_PATH))

    if len(argv) > 1:
        filename = argv[1]
        filename = ' '.join(argv[1:])

        run_file_decryption(filename)
    else:
        run_sync_daemon()
