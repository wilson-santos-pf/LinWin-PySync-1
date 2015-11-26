from pprint import pprint
from os import listdir
from os.path import isdir
from os import stat
from os.path import join

class MetaVFS(object):
    def __init__(self, modified_at=None, path=None, is_dir=None, children=None):
        self.path = path
        self.is_dir = is_dir
        self.modified_at = modified_at
        self.children = children
        if self.children is None:
            self.children = []
        self.parent = None

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def debug_print(self):
        print self.path
        for child in self.children:
            child.debug_print()

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
        self.populate_filepath_metadata(path='.', parent=None)

    def populate_localbox_metadata(self, path='/', parent=None):
        node = self.localbox.get_meta(path)
        vfsnode = MetaVFS(node['modified_at'], node['path'], node['is_dir'])
        for child in node['children']:
            self.populate_localbox_metadata(child['path'], parent=vfsnode)
        if parent is None:
            self.localbox_metadata = vfsnode
        else:
            parent.add_child(vfsnode)

    def populate_filepath_metadata(self, path='.', parent=None):
        realpath = join(self.filepath, path)
        print "processing " + path + " transformed to " + realpath
        is_dir = isdir(realpath)
        modtime = stat(realpath).st_mtime
        vfsnode = MetaVFS(modtime, path, is_dir)

        for entry in listdir(realpath):
            self.populate_filepath_metadata(join(path, entry), parent=vfsnode)
        if parent is None:
            self.filepath_metadata = vfsnode
        else:
            parent.add_child(vfsnode)




        
