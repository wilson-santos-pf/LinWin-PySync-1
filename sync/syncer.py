from os import listdir
from pprint import pprint
from os import remove
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
from cPickle import dump, load

class MetaVFS(object):
    def __init__(self, modified_at=None, path=None, is_dir=None, children=None):
        self.path = path
        self.is_dir = is_dir
        self.modified_at = modified_at
        self.children = children
        if self.children is None:
            self.children = []
        self.parent = None

    def get_paths(self):
        paths = [self.path]
        for child in self.children:
            paths += child.get_paths()
        return paths

    def save(self, filename):
        fd = open(filename, 'w')
        dump(self, fd)
        fd.close()

    def load(self,filename):
        fd = open(filename, 'r')
        value = load(fd)
        fd.close()
        return value


    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def debug_print(self):
        print self.path
        for child in self.children:
            child.debug_print()

    def yield_directories(self):
        if self.is_dir:
            yield(self)
            for child in self.children:
                for result in child.yield_directories():
                    yield result

    def yield_files(self):
        if not self.is_dir:
            yield(self)
        for child in self.children:
            for result in child.yield_files():
                yield result

    def get_entry(self, path):
        for entry in chain(self.yield_directories(), self.yield_files()):
            if entry.path == path:
                return entry
        return None

    def contains_directory(self, filepath):
        if len(filepath) > 0 and filepath[0] == '.':
            print("removing superfluous '.'")
            filepath = filepath[1:]
        if len(filepath) == 0 or filepath[0] != '/':
            print("adding root '/' to path")
            filepath = '/' + filepath
        result = False
        print "MATCHING: " + filepath
        for vfsdirectory in self.yield_directories():
            directory = vfsdirectory.path
            print "TO      : " + directory
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
        if direction not in ['up', 'down', 'sync']:
            raise ValueError("direction needs to be either 'up', 'down' or 'sync'")
        self.direction = direction
        print "LocalBox:"
        self.populate_localbox_metadata(path='/', parent=None)
        print "Local FS:"
        self.populate_filepath_metadata(path='./', parent=None)

    def populate_localbox_metadata(self, path='/', parent=None):
        node = self.localbox.get_meta(path)
        splittime = node['modified_at'].split('.', 1)
        modtime = mktime(strptime(splittime[0], "%Y-%m-%dT%H:%M:%S")) + float("0."+splittime[1])
        vfsnode = MetaVFS(modtime, node['path'], node['is_dir'])
        for child in node['children']:
            self.populate_localbox_metadata(child['path'], parent=vfsnode)
        if parent is None:
            self.localbox_metadata = vfsnode
        else:
            parent.add_child(vfsnode)

    def populate_filepath_metadata(self, path='./', parent=None):
        if path == '.':
            path = './'
        realpath = abspath(join(self.filepath, path))
        print "processing " + path + " transformed to " + realpath
        is_dir = isdir(realpath)
        modtime = stat(realpath).st_mtime
        vfsnode = MetaVFS(modtime, path[1:], is_dir)

        if is_dir:
            for entry in listdir(realpath):
                self.populate_filepath_metadata(join(path, entry), parent=vfsnode)
        if parent is None:
            self.filepath_metadata = vfsnode
        else:
            parent.add_child(vfsnode)

    def downsync(self):
        for vfsdirname in self.localbox_metadata.yield_directories():
            dirname = join(self.filepath, "." + vfsdirname.path)
            if not isdir(dirname):
                mkdir(dirname)
        for vfsfilename in self.localbox_metadata.yield_files():
            filename = vfsfilename.path
            print "processing file " + filename
            localfile = self.filepath_metadata.get_entry(filename)
            remotefile = self.localbox_metadata.get_entry(filename)
            if localfile is None or (remotefile != None and localfile.modified_at < remotefile.modified_at + 2):
                print "downloading " + filename
                contents = self.localbox.get_file(filename)
                localfilename = join(self.filepath, filename[1:])
                localfile = open(localfilename, 'w')
                localfile.write(contents)
                localfile.close()
                utime(localfilename, (time(), self.localbox_metadata.get_entry(filename).modified_at))
            else:
                print "Already downloaded " + filename
        self.filepath_metadata.save('localbox.pickle')

    def upsync(self):
        for vfsdirname in self.filepath_metadata.yield_directories():
            dirname = vfsdirname.path
            print "processing " + dirname
            #dirname = join(self.filepath, "." + dirname)
            if not self.localbox_metadata.contains_directory(dirname):
                print "creating directory " + dirname
                self.localbox.create_directory(dirname)

        for vfsfilename in self.filepath_metadata.yield_files():
            filename = vfsfilename.path
            print "processing file " + filename
            remote = self.localbox_metadata.get_entry(filename)
     
            if remote is None or self.filepath_metadata.get_entry(filename).modified_at + 2 > self.localbox_metadata.get_entry(filename).modified_at:
                print "uploading " + filename
                self.localbox.upload_file(filename, join(self.filepath, filename[1:]))
            else:
                print "Already uploaded " + filename

        print self.filepath_metadata.debug_print()
        filename="testfile"
        self.filepath_metadata.save(filename)
        newthing = self.filepath_metadata.load(filename)
        print(newthing)
        self.filepath_metadata.debug_print()

    def syncsync(self):
        allpaths = set(self.filepath_metadata.get_paths() + self.localbox_metadata.get_paths())
        try:
            oldmetadata = self.filepath_metadata.load('localbox.pickle')
            allpaths = set(list(allpaths) + oldmetadata.get_paths())
        except IOError:
            print "Old data unknown"
            oldmetadata =  MetaVFS(path='/', modified_at=0)
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
                if not localfile.is_dir and (localfile.modified_at - remotefile.modified_at) > 2:
                    self.localbox.upload_file(path, join(self.filepath, path[1:]))
                if not localfile.is_dir and (remotefile.modified_at - localfile.modified_at) > 2:
                    contents = self.localbox.get_file(path)
                    localfilename = join(self.filepath, path[1:])
                    localfile = open(localfilename, 'w')
                    localfile.write(contents)
                    localfile.close()
                    utime(localfilename, (time(), self.localbox_metadata.get_entry(path).modified_at))
            if oldfile is None:
                if remotefile is not None and (localfile is None or localfile.modified_at + 2 < remotefile.modified_at) and not remotefile.is_dir:
                    contents = self.localbox.get_file(path)
                    localfilename = join(self.filepath, path[1:])
                    localfile = open(localfilename, 'w')
                    localfile.write(contents)
                    localfile.close()
                    utime(localfilename, (time(), self.localbox_metadata.get_entry(path).modified_at))
                elif remotefile is not None and localfile is None and remotefile.is_dir:
                    mkdir(join(self.filepath, path[1:]))
                elif remotefile is None or (localfile.modified_at > remotefile.modified_at + 2):
                    if localfile.is_dir and remotefile is None:
                        self.localbox.create_directory(path)
                    elif not localfile.is_dir:
                        self.localbox.upload_file(path, join(self.filepath, path[1:]))
                else:
                    assert localfile.is_dir or remotefile.is_dir or (abs(localfile.modified_at - remotefile.modified_at) < 2)
            elif oldfile is not None:
                if localfile is None and remotefile is not None:
                    self.localbox.delete(path)
                if localfile is not None and remotefile is None:
                    filepath = join(self.filepath, path[1:])
                    if isdir(filepath):
                        rmtree(filepath)
                    else:
                        remove(filepath)
            else:
                raise(Error("unreachable"))
        self.filepath_metadata.save('localbox.pickle')
