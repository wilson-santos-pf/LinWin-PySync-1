from os import listdir
from os import remove
from logging import getLogger
from os import utime
from shutil import rmtree
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
try:
    from urllib2 import HTTPError
    from cPickle import dump, load
except ImportError:
    from urllib.error import HTTPError
    from pickle import dump, load

from .defaults import OLD_SYNC_STATUS


class MetaVFS(object):
    """
    virtual meta filesystem
    """

    def __init__(self, modified_at=None, path=None, is_dir=None,
                 children=None):
        self.path = path
        self.is_dir = is_dir
        self.modified_at = modified_at
        self.children = children
        if self.children is None:
            self.children = []
        self.parent = None

    def get_paths(self):
        """
        return all paths contained in this filesystem
        """
        paths = [self.path]
        for child in self.children:
            paths += child.get_paths()
        return paths

    def save(self, filename):
        """
        save this MetaVFS into a file
        """
        filedescriptor = open(filename, 'w')
        dump(self, filedescriptor)
        filedescriptor.close()

    def load(self, filename):
        """
        load this metvfs into a file
        """
        filedescriptor = open(filename, 'r')
        value = load(filedescriptor)
        filedescriptor.close()
        return value

    def add_child(self, child):
        """
        add a child to this node, also set child's parent
        """
        self.children.append(child)
        child.parent = self

    def debug_print(self):
        """
        do a debug pring of all paths
        """
        getLogger('localbox').info(self.path)
        for child in self.children:
            child.debug_print()

    def yield_directories(self):
        """
        return a directory part of this metavfs
        """
        if self.is_dir:
            yield self
            for child in self.children:
                for result in child.yield_directories():
                    yield result

    def yield_files(self):
        """
        return a file part of this metavfs
        """
        if not self.is_dir:
            yield self
        for child in self.children:
            for result in child.yield_files():
                yield result

    def get_entry(self, path):
        """
        return an entry (file or directory) from the system
        """
        for entry in chain(self.yield_directories(), self.yield_files()):
            if entry.path == path:
                return entry
        return None

    def contains_directory(self, filepath):
        """
        is a certain path in this vfs directory structure?
        """
        if len(filepath) > 0 and filepath[0] == '.':
            getLogger('localbox').info("removing superfluous '.'")
            filepath = filepath[1:]
        if len(filepath) == 0 or filepath[0] != '/':
            getLogger('localbox').info("adding root '/' to path")
            filepath = '/' + filepath
        result = False
        getLogger('localbox').info("MATCHING: " + filepath)
        for vfsdirectory in self.yield_directories():
            directory = vfsdirectory.path
            getLogger('localbox').info("TO      : " + directory)
            if directory == filepath:
                result = True
                break
        return result


class Syncer(object):
    def __init__(self, localbox_instance, file_root_path, direction):
        self.localbox = localbox_instance
        self.filepath = file_root_path
        self.localbox_metadata = None
        self.filepath_metadata = None
        self.direction = direction
        getLogger('localbox').info("LocalBox:")
        self.populate_localbox_metadata(path='/', parent=None)
        getLogger('localbox').info("Local FS:")
        self.populate_filepath_metadata(path='./', parent=None)

    def populate_localbox_metadata(self, path='/', parent=None):
        node = self.localbox.get_meta(path)
        splittime = node['modified_at'].split('.', 1)
        modtime = mktime(strptime(splittime[0], "%Y-%m-%dT%H:%M:%S")) + \
            float("0."+splittime[1])
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
        realpath = abspath(join(self.filepath, path))
        getLogger('localbox').info("processing " + path + " transformed to "
                                   + realpath)
        is_dir = isdir(realpath)
        modtime = stat(realpath).st_mtime
        vfsnode = MetaVFS(modtime, path[1:], is_dir)

        if is_dir:
            for entry in listdir(realpath):
                self.populate_filepath_metadata(join(path, entry),
                                                parent=vfsnode)
        if parent is None:
            self.filepath_metadata = vfsnode
        else:
            parent.add_child(vfsnode)

    def downsync(self):
        for vfsdirname in self.localbox_metadata.yield_directories():
            dirpath = join(self.filepath, "." + vfsdirname.path)
            if not isdir(dirpath):
                mkdir(dirpath)
        for vfsfilename in self.localbox_metadata.yield_files():
            filename = vfsfilename.path
            getLogger('localbox').info("processing file " + filename)
            localfile = self.filepath_metadata.get_entry(filename)
            remotefile = self.localbox_metadata.get_entry(filename)
            if localfile is None or (remotefile is not None and
                                     localfile.modified_at <
                                     remotefile.modified_at + 2):
                getLogger('localbox').info("downloading " + filename)
                contents = self.localbox.get_file(filename)
                localfilename = join(self.filepath, filename[1:])
                localfile = open(localfilename, 'w')
                localfile.write(contents)
                localfile.close()
                localfilepath = self.localbox_metadata.get_entry(filename)
                modtime = localfilepath.modified_at
                utime(localfilename, (time(), modtime))
            else:
                getLogger('localbox').info("Already downloaded " + filename)
        self.filepath_metadata.save(OLD_SYNC_STATUS)

    def upsync(self):
        for vfsdirname in self.filepath_metadata.yield_directories():
            dirpath = vfsdirname.path
            getLogger('localbox').info("processing " + dirpath)
            # dirname = join(self.filepath, "." + dirpath)
            if not self.localbox_metadata.contains_directory(dirpath):
                getLogger('localbox').info("creating directory " + dirpath)
                self.localbox.create_directory(dirpath)

        for vfsfilename in self.filepath_metadata.yield_files():
            filename = vfsfilename.path
            getLogger('localbox').info("processing file " + filename)
            remote = self.localbox_metadata.get_entry(filename)
            remotetime = self.localbox_metadata.get_entry(filename).modified_at
            localtime = self.filepath_metadata.get_entry(filename).modified_at
            if remote is None or localtime + 2 > remotetime:
                getLogger('localbox').info("uploading " + filename)
                self.localbox.upload_file(filename, join(self.filepath,
                                                         filename[1:]))
            else:
                getLogger('localbox').info("Already uploaded " + filename)

        self.filepath_metadata.save(OLD_SYNC_STATUS)
        # self.filepath_metadata.load(OLD_SYNC_STATUS)
        self.filepath_metadata.debug_print()

    def syncsync(self):
        getLogger('localbox').info("Starting syncsync")
        allpaths = set(self.filepath_metadata.get_paths() +
                       self.localbox_metadata.get_paths())
        self.filepath_metadata.debug_print()
        self.localbox_metadata.debug_print()
        getLogger('localbox').info(str(allpaths))
        try:
            oldmetadata = self.filepath_metadata.load(OLD_SYNC_STATUS)
            allpaths = set(list(allpaths) + oldmetadata.get_paths())
        except IOError:
            getLogger('localbox').info("Old data unknown")
            oldmetadata = MetaVFS(path='/', modified_at=0)
        deleted_folders = []
        for path in sorted(allpaths):
            skip = False
            for entry in deleted_folders:
                if path.startswith(entry):
                    skip = True
            if skip:
                continue
            oldfile = oldmetadata.get_entry(path)
            localfile = self.filepath_metadata.get_entry(path)
            remotefile = self.localbox_metadata.get_entry(path)

            if localfile is not None and remotefile is not None:
                if not localfile.is_dir and (localfile.modified_at -
                                             remotefile.modified_at) > 2:
                    self.localbox.upload_file(path, join(self.filepath,
                                                         path[1:]))
                if (not localfile.is_dir and (remotefile.modified_at -
                                              localfile.modified_at) > 2):
                    contents = self.localbox.get_file(path)
                    localfilename = join(self.filepath, path[1:])
                    localfile = open(localfilename, 'w')
                    localfile.write(contents)
                    localfile.close()
                    localfilepath = self.localbox_metadata.get_entry(path)
                    modtime = localfilepath.modified_at
                    utime(localfilename, (time(), modtime))
                    continue
            if oldfile is None:
                if (remotefile is not None and
                    (localfile is None or localfile.modified_at + 2 <
                     remotefile.modified_at) and not remotefile.is_dir):
                    contents = self.localbox.get_file(path)
                    localfilename = join(self.filepath, path[1:])
                    localfile = open(localfilename, 'w')
                    localfile.write(contents)
                    localfile.close()
                    localfilepath = self.localbox_metadata.get_entry(path)
                    modtime = localfilepath.modified_at
                    utime(localfilename, (time(), modtime))
                elif (remotefile is not None and localfile is None and
                      remotefile.is_dir):
                    try:
                        mkdir(join(self.filepath, path[1:]))
                    # this may happen with precreated directories
                    except OSError:
                        pass
                elif (remotefile is None or
                      (localfile.modified_at > remotefile.modified_at + 2)):
                    if localfile.is_dir and remotefile is None:
                        self.localbox.create_directory(path)
                    elif not localfile.is_dir:
                        self.localbox.upload_file(path, join(self.filepath,
                                                             path[1:]))
                else:
                    diff = localfile.modified_at - remotefile.modified_at
                    assert (localfile.is_dir or remotefile.is_dir or
                            (abs(diff) < 2))
            elif oldfile is not None:
                if localfile is None and remotefile is not None:
                    try:
                        # self.localbox.delete(path)
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
                    except HTTPError:
                        # happens when the containing directory has already
                        # been deleted. Could do with more elegant syncing,
                        # but is otherwise harmless.
                        pass
                if localfile is not None and remotefile is None:
                    try:
                        filepath = join(self.filepath, path[1:])
                        if isdir(filepath):
                            rmtree(filepath)
                        else:
                            remove(filepath)
                    except HTTPError:
                        pass
            else:
                raise(Exception("unreachable"))
        self.filepath_metadata.save(OLD_SYNC_STATUS)
