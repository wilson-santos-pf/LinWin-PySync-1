from logging import getLogger
from itertools import chain
from copy import deepcopy
from os.path import sep
try:
    from cPickle import dump, load
except ImportError:
    from pickle import dump, load

import sync.defaults as defaults


def normalize_path(path):
    if path == '':
        return '/'
    path = path.replace(sep, '/')
    if path[0] == '.':
        path = path[1:]
    if path == '':
        path = '/'
    if path[0] != '/':
        path = '/' + path
    return path


class MetaVFS(object):

    """
    virtual meta filesystem
    """

    def __init__(self, modified_at=None, path=None, is_dir=None,
                 children=None):
        path=path.encode('utf-8')
        self.path = normalize_path(path)
        if self.path != path:
            getLogger(__name__).debug(
                "MetaVFS writing %s as %s", path, self.path)
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
        if other is None:
            return False
        return abs(self.modified_at - other.modified_at) <= 2

    def __ne__(self, other):
        return not self.__eq__(other)

    def gen(self):
        getLogger(__name__).debug("Yielding %s", self)
        yield self
        for child in self.children:
            for entry in child.gen():
                # y=child.gen()
                yield entry

    def add_paths(self, other):
        for kid in other.children:
            if kid.path not in self.get_paths():
                self.add_child(deepcopy(kid))
            else:
                entry = self.get_entry(kid.path)
                entry.add_paths(kid)
        return self

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
        getLogger(__name__).info('saving state to %s', filename)
        filedescriptor = open(filename, 'w')
        dump(self, filedescriptor)
        filedescriptor.close()

    def load(self, filename):
        """
        load this metvfs from a file
        """
        getLogger(__name__).info('loading state from %s', filename)
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
