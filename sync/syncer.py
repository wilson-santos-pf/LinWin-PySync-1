import os
from os import listdir
from os import remove
from logging import getLogger
from os import utime
from shutil import rmtree
from os.path import isdir
from os import stat
from os.path import join
from os.path import abspath
from itertools import chain
from threading import Thread, Lock
from time import mktime
from time import strptime
from time import time
from time import sleep
from os.path import exists
from os.path import dirname
from os import makedirs
from os import sep

from loxcommon import os_utils
from sync import defaults
from sync.controllers.login_ctrl import LoginController
from sync.gui import gui_utils
from sync.gui.gui_wx import PassphraseDialog
from .defaults import OLD_SYNC_STATUS
from .metavfs import MetaVFS


class Syncer(object):
    def __init__(self, localbox_instance, file_root_path, direction, name=None):
        self.localbox = localbox_instance
        self.name = name
        self.filepath = file_root_path.replace('/', sep)
        self.localbox_metadata = None
        self.filepath_metadata = None
        self.direction = direction

    def get_file_path(self, metavfs_entry):
        """
        System local filename
        :param metavfs_entry:
        :return:
        """
        path = metavfs_entry.path.split('/')
        return join(self.filepath, *path)

    def get_url_path(self, metavfs_entry):
        # path begins with '/', urls end in '/', one of these has got to go
        return self.localbox.url + metavfs_entry.path[1:]

    def populate_localbox_metadata(self, path='/', parent=None):
        node = self.localbox.get_meta(path)
        getLogger(__name__).debug('populate_localbox_metadata node: %s' % node)
        splittime = node['modified_at'].split('.', 1)
        modtime = mktime(strptime(splittime[0], "%Y-%m-%dT%H:%M:%S")) + \
                  float("0." + splittime[1])
        getLogger(__name__).debug('%s remote modification time: %s' % (path, modtime))
        vfsnode = MetaVFS(modtime, node['path'], node['is_dir'])
        for child in node['children']:
            self.populate_localbox_metadata(child['path'], parent=vfsnode)
        if parent is None:
            self.localbox_metadata = vfsnode
        else:
            getLogger(__name__).debug("parent %s gets child %s" % (parent, vfsnode))
            parent.add_child(vfsnode)

    def populate_filepath_metadata(self, path='/', parent=None):
        path = path.lstrip('.').rstrip("/\\")
        getLogger(__name__).debug('populate_filepath_metadata: %s' % path)
        if path == '':
            realpath = self.filepath
        else:
            realpath = join(self.filepath, path)
        getLogger(__name__).info("processing " + path + " transformed to "
                                 + realpath)
        is_dir = isdir(realpath)

        path_dec = os_utils.remove_extension(path, defaults.LOCALBOX_EXTENSION)
        realpath_dec = os_utils.remove_extension(realpath, defaults.LOCALBOX_EXTENSION)
        if is_dir:
            modtime = os.path.getmtime(realpath)
            vfsnode = MetaVFS(modtime, path_dec, is_dir)
            for entry in listdir(realpath):
                self.populate_filepath_metadata(join(path, entry), parent=vfsnode)
        else:
            if not path.endswith(defaults.LOCALBOX_EXTENSION):
                if not os.path.exists(realpath + defaults.LOCALBOX_EXTENSION):
                    modtime = os.path.getmtime(realpath)
                else:
                    return
            else:
                if os.path.exists(realpath_dec):
                    modtime_enc = os.path.getmtime(realpath)
                    modtime_dec = os.path.getmtime(realpath_dec)
                    modtime = modtime_dec if modtime_dec > modtime_enc else modtime_enc
                else:
                    modtime = os.path.getmtime(realpath)

            vfsnode = MetaVFS(modtime, path_dec, is_dir)

        if parent is None:
            self.filepath_metadata = vfsnode
        else:
            parent.add_child(vfsnode)

    def mkdir(self, metavfs):
        localfilename = self.get_file_path(metavfs)
        makedirs(localfilename)

    def delete(self, path):
        # join(self.filepath, path[1:])
        localfilename = self.get_file_path(path)
        if isdir(localfilename):
            rmtree(localfilename)
        else:
            try:
                # remove(localfilename)
                remove(localfilename + defaults.LOCALBOX_EXTENSION)
            except OSError:
                getLogger(__name__).info("Already deleted " + localfilename)

    def download(self, path):
        contents = self.localbox.get_file(path)
        if contents is not None:
            localfilename_noext = join(self.filepath, path[1:])
            localfilename = localfilename_noext + defaults.LOCALBOX_EXTENSION
            # precreate folder if needed
            localdirname = dirname(localfilename)
            if not exists(localdirname):
                makedirs(localdirname)

            # save new encrypted file to disk
            getLogger(__name__).debug('Saving to disk: %s' % localfilename)
            localfile = open(localfilename, 'wb')
            localfile.write(contents)
            localfile.close()

            # delete old decrypted file
            if exists(localfilename_noext):
                os.remove(localfilename_noext)

            localfilepath = self.localbox_metadata.get_entry(path)
            modtime = localfilepath.modified_at
            utime(localfilename, (time(), modtime))
        else:
            getLogger(__name__).error('Failed to download %s' % path)

    def syncsync(self):
        label = self.localbox.authenticator.label
        getLogger(__name__).info("Starting syncsync")

        # get passphrase
        getLogger(__name__).debug('waiting for passphrase, label=%s' % label)
        passphrase = LoginController().get_passphrase(label)
        while not passphrase:
            sleep(1)
            passphrase = LoginController().get_passphrase(label)

        getLogger(__name__).debug('got passphrase for label=%s' % label)

        self.localbox_metadata = None
        self.filepath_metadata = None
        self.populate_localbox_metadata(path='/', parent=None)
        self.populate_filepath_metadata(path='/', parent=None)

        # directories = set(chain(self.filepath_metadata.yield_directories(
        # ), self.localbox_metadata.yield_directories()))
        # self.dirsync(directories)
        # allpaths = set(self.filepath_metadata.get_files() +
        #               self.localbox_metadata.get_files())
        full_tree = MetaVFS('0', '/', True, None)
        full_tree.add_paths(self.localbox_metadata)
        full_tree.add_paths(self.filepath_metadata)

        try:
            oldmetadata = self.filepath_metadata.load(
                OLD_SYNC_STATUS + self.name)
            full_tree.add_paths(oldmetadata)
        except (IOError, AttributeError) as error:
            getLogger(__name__).info(str(error) + " Using empty tree instead")
            oldmetadata = MetaVFS(path='/', modified_at=0)

        for metavfs in full_tree.gen():
            try:
                path = metavfs.path

                oldfile = oldmetadata.get_entry(path)
                localfile = self.filepath_metadata.get_entry(path)
                remotefile = self.localbox_metadata.get_entry(path)
                getLogger(__name__).debug(
                    "====Local %s, Remote %s, Old %s ====", localfile, remotefile, oldfile)

                # if remotefile == oldfile and self.get_file_path(metavfs)is None:
                if remotefile == oldfile and localfile is None:
                    self.localbox.delete(metavfs)
                    getLogger(__name__).info("Deleting remote %s", path)
                    continue
                # if localfile == oldfile and self.get_url_path(metavfs) is None:
                if localfile == oldfile and remotefile is None:
                    getLogger(__name__).info("Deleting local %s", path)
                    self.delete(metavfs)
                    continue

                newest = MetaVFS.newest(oldfile, localfile, remotefile)

                if newest == oldfile and newest is not None:
                    getLogger(__name__).info(
                        "Skipping %s because all files are older then the previous file", newest.path)
                    continue

                newest = MetaVFS.newest(localfile, remotefile)

                localpath = self.get_file_path(metavfs)
                if newest == localfile and os.path.exists(localpath):
                    # TODO: Only create directorieswhen needed, preferably not.
                    if dirname(path) not in self.localbox_metadata.get_paths():
                        self.localbox.create_directory(dirname(path))

                    if not isdir(self.get_file_path(metavfs)):
                        getLogger(__name__).info("Uploading %s:  %s", newest.path, localpath)

                        self.localbox.upload_file(path, localpath, passphrase)
                    elif path != '/':
                        self.localbox.create_directory(path)
                    continue
                if newest == remotefile:
                    getLogger(__name__).info("%s is_dir: %s", metavfs.path, metavfs.is_dir)
                    if not metavfs.is_dir:
                        getLogger(__name__).info("Downloading %s", newest.path)
                        self.download(path)
                    else:
                        if not isdir(self.get_file_path(metavfs)):
                            self.mkdir(metavfs)

                    continue
            except Exception as error:
                getLogger(__name__).exception("Problem '%s' with file %s; continuing", error, metavfs.path)
        self.populate_filepath_metadata(path='./', parent=None)
        self.filepath_metadata.save(OLD_SYNC_STATUS + self.name)


class SyncRunner(Thread):
    """
    Thread responsible for synchronizing between the client and one server.
    """

    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None, verbose=None, syncer=None):
        Thread.__init__(self, group=group, target=target, name=name,
                        args=args, kwargs=kwargs, verbose=verbose)
        self.setDaemon(True)
        self.syncer = syncer
        self.lock = Lock()

    def run(self):
        """
        Function that runs one iteration of the synchronization
        """
        getLogger(__name__).info("SyncRunner " + self.name + " started")
        self.lock.acquire()
        self.syncer.syncsync()
        self.lock.release()
        getLogger(__name__).info("SyncRunner " + self.name + " finished")

    @property
    def name(self):
        return 'th-' + self.syncer.name
