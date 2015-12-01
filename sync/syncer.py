from os import listdir
from os import utime
from os.path import isdir
from os import stat
from os.path import join
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
        realpath = join(self.filepath, path)
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
            if self.filepath_metadata.get_entry(filename).modified_at < self.localbox_metadata.get_entry(filename).modified_at + 2:
                print "downloading " + filename
                contents = self.localbox.get_file(filename)
                localfilename = join(self.filepath, filename[1:])
                localfile = open(localfilename, 'w')
                localfile.write(contents)
                localfile.close()
                utime(localfilename, (time(), self.localbox_metadata.get_entry(filename).modified_at))
            else:
                print "Already downloaded " + filename

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



