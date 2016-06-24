from os import listdir
from os import remove
from os import removedirs
from logging import getLogger
from os import utime
from shutil import rmtree #TODO: remove directories
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

    def __str__(self):
        return self.path

    def __lt__(self, other):  # <
        return self.modified_at < other.modified_at

    def __le__(self, other):  # <=
        return self.modified_at <= other.modified_at

    def __gt__(self, other):  # >
        return self.modified_at > other.modified_at

    def __ge__(self, other):  # >=
        return self.modified_at >= other.modified_at

    def __eq__(self, other):  # ==
        """
        Equality check. Due to the fact FAT has a 2 second resolution on
        writing, and NTFS seems to have followed this, two files are considered
        'equal' in that respect if their modified times are at most two seconds
        apart. See
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms724290%28v=vs.85%29.aspx
        """
        if other == None:
            return False
        return abs(self.modified_at - other.modified_at) <= 2

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def newest(*arguments):
        """
        Returns the one single MetaVFS entry of the three with the highest
        modified time. Returns None otherwise, including when two are tied for
        highest modification time.
        """
        args = [item for item in arguments if item is not None]
        unique = True
        current = args[0]
        print(current)
        for entry in args[1:]:
            if entry is None:
                continue
            if entry == current:
                unique = False
            elif entry > current:
                current = entry
                unique = True
        if unique:
            return current
        else:
            return None

    def get_paths(self):
        """
        return all paths contained in this filesystem
        """
        paths = [self.path]
        for child in self.children:
            paths += child.get_paths()
        return paths

    def get_files(self):
        """
        return all paths to files (not directories) contained in this filesystem
        """
        if not self.is_dir:
            paths = [self.path]
        else:
            paths = []
        for child in self.children:
            paths += child.get_files()
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
        try:
            filedescriptor = open(filename, 'r')
            value = load(filedescriptor)
            filedescriptor.close()
            return value
        except IOError:
            return None

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
        getLogger(__name__).info(self.path)
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
            getLogger(__name__).info("removing superfluous '.'")
            filepath = filepath[1:]
        if len(filepath) == 0 or filepath[0] != '/':
            getLogger(__name__).info("adding root '/' to path")
            filepath = '/' + filepath
        result = False
        getLogger(__name__).info("MATCHING: " + filepath)
        for vfsdirectory in self.yield_directories():
            directory = vfsdirectory.path
            getLogger(__name__).info("TO      : " + directory)
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
        realpath = abspath(join(self.filepath, path))
        getLogger(__name__).info("processing " + path + " transformed to "
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
            getLogger(__name__).info("processing file " + filename)
            localfile = self.filepath_metadata.get_entry(filename)
            remotefile = self.localbox_metadata.get_entry(filename)
            if localfile is None or (remotefile is not None and
                                     localfile.modified_at <
                                     remotefile.modified_at + 2):
                getLogger(__name__).info("downloading " + filename)
                self.download(filename)
            else:
                getLogger(__name__).info("Already downloaded " + filename)
        self.filepath_metadata.save(OLD_SYNC_STATUS)

    def upsync(self):
        for vfsdirname in self.filepath_metadata.yield_directories():
            dirpath = vfsdirname.path
            getLogger(__name__).info("processing " + dirpath)
            # dirname = join(self.filepath, "." + dirpath)
            if not self.localbox_metadata.contains_directory(dirpath):
                getLogger(__name__).info("creating directory " + dirpath)
                self.localbox.create_directory(dirpath)

        for vfsfilename in self.filepath_metadata.yield_files():
            filename = vfsfilename.path
            getLogger(__name__).info("processing file " + filename)
            remote = self.localbox_metadata.get_entry(filename)
            remotetime = self.localbox_metadata.get_entry(filename).modified_at
            localtime = self.filepath_metadata.get_entry(filename).modified_at
            if remote is None or localtime + 2 > remotetime:
                getLogger(__name__).info("uploading " + filename)
                self.localbox.create_directory(dirname(filename))
                self.localbox.upload_file(filename, join(self.filepath,
                                                         filename[1:]))
            else:
                getLogger(__name__).info("Already uploaded " + filename)

        self.filepath_metadata.save(OLD_SYNC_STATUS)
        # self.filepath_metadata.load(OLD_SYNC_STATUS)
        self.filepath_metadata.debug_print()

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
        oldmetadata = self.filepath_metadata.load(OLD_SYNC_STATUS)
        if oldmetadata is None:
            oldmetadata = MetaVFS(path='/', modified_at=0)

        for directory in directories:
            directory = str(directory)
            olddir = oldmetadata.get_entry(directory)
            localdir = self.filepath_metadata.get_entry(directory)
            remotedir = self.localbox_metadata.get_entry(directory)
            print("====Local %s, Remote %s, Old %s ====" % (localdir, remotedir, olddir))
            if olddir is not None and localdir is None:
                self.localbox.delete(directory)
            if olddir is not None and remotedir is None:
                self.delete(directory)
            if olddir is None and localdir is None:
                try:
                    self.mkdir(directory)
                except OSError as error:
                    getLogger(__name__).info("OSError when creating folder %s: %s", directory ,error)
            if olddir is None and remotedir is None:
                self.localbox.create_directory(directory)

    def syncsync(self):
        getLogger(__name__).info("Starting syncsync")
        getLogger(__name__).info("LocalBox:")
        self.populate_localbox_metadata(path='/', parent=None)
        getLogger(__name__).info("Local FS:")
        self.populate_filepath_metadata(path='./', parent=None)
        directories = set(chain(self.filepath_metadata.yield_directories(), self.localbox_metadata.yield_directories()))
        self.dirsync(directories)
        allpaths = set(self.filepath_metadata.get_files() +
                       self.localbox_metadata.get_files())
        self.filepath_metadata.debug_print()
        self.localbox_metadata.debug_print()

        try:
            oldmetadata = self.filepath_metadata.load(OLD_SYNC_STATUS)
            allpaths = set(list(allpaths) + oldmetadata.get_files())
        except (IOError, AttributeError) as error:
            getLogger(__name__).info("Old data unknown")
            getLogger(__name__).exception(error)
            oldmetadata = MetaVFS(path='/', modified_at=0)
        getLogger(__name__).info(str(allpaths))

        for path in sorted(allpaths):
            print("Syncing %s" % path)
            oldfile = oldmetadata.get_entry(path)
            localfile = self.filepath_metadata.get_entry(path)
            remotefile = self.localbox_metadata.get_entry(path)

            if remotefile == oldfile and localfile is None:
                self.localbox.delete(path)
                getLogger(__name__).info("Deleting remote %s", path)
                continue
            if localfile == oldfile and remotefile is None:
                print(path)
                getLogger(__name__).info("Deleting local %s", path)
                self.delete(path)
                continue

            newest = MetaVFS.newest(oldfile, localfile, remotefile)
            print("====Newest %s, Local %s, Remote %s, Old %s ====" % (newest, localfile, remotefile, oldfile))

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

        self.filepath_metadata.save(OLD_SYNC_STATUS)
