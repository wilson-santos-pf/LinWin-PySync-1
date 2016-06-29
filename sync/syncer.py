from os import listdir
from os import remove
from os import removedirs
from logging import getLogger
from os import utime
from shutil import rmtree  # TODO: remove directories
from os.path import isdir
from os import stat
from os.path import join
from os.path import abspath
from os import mkdir
from itertools import chain
from time import mktime
from time import strptime
from time import time
from os.path import exists
from os.path import dirname
from os import makedirs
from os.path import sep
try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

from .defaults import OLD_SYNC_STATUS
from .metavfs import MetaVFS

class Syncer(object):

    def __init__(self, localbox_instance, file_root_path, direction, name=None):
        self.localbox = localbox_instance
        self.name = name
        self.filepath = file_root_path
        self.localbox_metadata = None
        self.filepath_metadata = None
        self.direction = direction
        getLogger(__name__).info("LocalBox:")
        self.populate_localbox_metadata(path='/', parent=None)
        getLogger(__name__).info("Local FS:")
        self.populate_filepath_metadata(path='./', parent=None)

    def populate_localbox_metadata(self, path='/', parent=None):
        node = self.localbox.get_meta(path)
        splittime = node['modified_at'].split('.', 1)
        modtime = mktime(strptime(splittime[0], "%Y-%m-%dT%H:%M:%S")) + \
            float("0." + splittime[1])
        vfsnode = MetaVFS(modtime, node['path'], node['is_dir'])
        print("VFSNode Problematica")
        vfsnode.debug_print()
        print("END VFSNode Problematica")
        for child in node['children']:
            print("recursing")
            self.populate_localbox_metadata(child['path'], parent=vfsnode)
        if parent is None:
            print("parent is none")
            self.localbox_metadata = vfsnode
        else:
            print("parent gets child")
            parent.add_child(vfsnode)

    def populate_filepath_metadata(self, path='./', parent=None):
        if path == '.':
            path = './'
        path = path.lstrip("/\\")
        realpath = abspath(join(self.filepath, path))
        print realpath
        getLogger(__name__).info("processing " + path + " transformed to "
                                 + realpath)
        is_dir = isdir(realpath)
        modtime = stat(realpath).st_mtime
        path = path.replace(sep, '/')
        if path[0] != '/':
            path = '/' + path
        if path[-1] == '/':
            path = path[:-1]
        vfsnode = MetaVFS(modtime, path[1:], is_dir)

        if is_dir:
            for entry in listdir(realpath):
                self.populate_filepath_metadata(join(path, entry),
                                                parent=vfsnode)
        if parent is None:
            self.filepath_metadata = vfsnode
        else:
            parent.add_child(vfsnode)

    def mkdir(self, path):
        localfilename = join(self.filepath, path[1:])
        makedirs(localfilename)

    def delete(self, path):
        localfilename = join(self.filepath, path[1:])
        if isdir(localfilename):
            rmtree(localfilename)
        else:
            try:
                remove(localfilename)
            except OSError:
                getLogger(__name__).info("Already deleted " + localfilename)

    def download(self, path):
        path = path.replace('/', sep)
        contents = self.localbox.get_file(path)
        localfilename = join(self.filepath, path[1:])
        # precreate folder if needed
        localdirname = dirname(localfilename)
        if not exists(localdirname):
            makedirs(localdirname)
        localfile = open(localfilename, 'w')
        localfile.write(contents)
        localfile.close()
        localfilepath = self.localbox_metadata.get_entry(path)
        modtime = localfilepath.modified_at
        utime(localfilename, (time(), modtime))

    def dirsync(self, directories):
        try:
            oldmetadata = self.filepath_metadata.load(
                OLD_SYNC_STATUS + self.name)
        except IOError:
            oldmetadata = MetaVFS(path='/', modified_at=0)

        for directory in directories:
            directory = str(directory)
            olddir = oldmetadata.get_entry(directory)
            localdir = self.filepath_metadata.get_entry(directory)
            remotedir = self.localbox_metadata.get_entry(directory)
            print("====Local %s, Remote %s, Old %s ====" %
                  (localdir, remotedir, olddir))
            if olddir is not None and localdir is None:
                self.localbox.delete(directory)
            if olddir is not None and remotedir is None:
                self.delete(directory)
            if olddir is None and localdir is None:
                try:
                    self.mkdir(directory)
                except OSError as error:
                    getLogger(__name__).info(
                        "OSError when creating folder %s: %s", directory, error)
            if olddir is None and remotedir is None:
                self.localbox.create_directory(directory)

    def syncsync(self):
        getLogger(__name__).info("Starting syncsync")
        getLogger(__name__).info("LocalBox:")
        self.populate_localbox_metadata(path='/', parent=None)
        getLogger(__name__).info("Local FS:")
        self.populate_filepath_metadata(path='./', parent=None)
        directories = set(chain(self.filepath_metadata.yield_directories(
        ), self.localbox_metadata.yield_directories()))
        self.dirsync(directories)
        allpaths = set(self.filepath_metadata.get_files() +
                       self.localbox_metadata.get_files())
        self.filepath_metadata.debug_print()
        self.localbox_metadata.debug_print()

        try:
            oldmetadata = self.filepath_metadata.load(
                OLD_SYNC_STATUS + self.name)
            allpaths = set(list(allpaths) + oldmetadata.get_files())
        except (IOError, AttributeError) as error:
            getLogger(__name__).info(str(error) + " Using empty tree instead")
            oldmetadata = MetaVFS(path='/', modified_at=0)
        getLogger(__name__).info(str(allpaths))

        for path in sorted(allpaths):
            if path[0] == ".":
                getLogger(__name__).debug("TODO: this removes the dot from './some/path/ext'; this should be done in the metavfs instead")
                path = path[1:]

            print("Syncing %s" % path)
            oldfile = oldmetadata.get_entry(path)
            localfile = self.filepath_metadata.get_entry(path)
            remotefile = self.localbox_metadata.get_entry(path)
            getLogger(__name__).debug("====Local %s, Remote %s, Old %s ====", localfile, remotefile, oldfile)

            if remotefile == oldfile and localfile is None:
                self.localbox.delete(path)
                getLogger(__name__).info("Deleting remote %s", path)
                continue
            if localfile == oldfile and remotefile is None:
                getLogger(__name__).info("Deleting local %s", path)
                self.delete(path)
                continue

            newest = MetaVFS.newest(oldfile, localfile, remotefile)
            print("====Newest %s, Local %s, Remote %s, Old %s ====" %
                  (newest, localfile, remotefile, oldfile))

            if newest == oldfile and newest is not None:
                getLogger(__name__).info(
                    "Skipping %s because all files are older then the previous file", newest.path)
                continue

            newest = MetaVFS.newest(localfile, remotefile)

            if newest == localfile:
                getLogger(__name__).info("Uploading %s", newest.path)
                # TODO: Only create directorieswhen needed, preferably not.
                if dirname(path) not in self.localbox_metadata.get_paths():
                    self.localbox.create_directory(dirname(path))

                self.localbox.upload_file(path, join(self.filepath,
                                                     path[1:]))
                continue
            if newest == remotefile:
                getLogger(__name__).info("Downloading %s", newest.path)
                self.download(path)
                continue

        self.filepath_metadata.save(OLD_SYNC_STATUS + self.name)
