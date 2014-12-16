import os
from error import LoxApiError
import datetime

class FileInfo:

    isdir = None
    modified = None
    size = None

class Kliekjes:

    def __init__(self,Api,Dir):
        pass

    def isdir():
        pass

    def modified():
        pass

    def size():
        pass

    def children():
        pass

    def encrypted():
        pass

    def hash():
        pass

class LoxLocal(FileInfo):

    def __init__(self,Dir):
        self.__Path = Dir

    def isdir():
        return os.path.isdir(FileInfo.__Path)

    def size():
        files = os.listdir(FileInfo.__Path)
        return len(files)

    def modified():
        mtime = os.path.getmtime(FileInfo.__Path)
        return datetime.fromtimestamp(mtime)

    def children(self,Account,Dir):
        files = set()
        for item in os.listdir(Dir):
            files.add(Dir+item)
        return files

    def hash():
        pass

class LoxRemote(FileInfo):

    def __init__(self,Session,Dir):
        self.__meta = Session.meta(Dir)

    def isdir(self):
        return self.__meta[u'is_dir']

    def size(self):
        return self.__meta[u'is_dir']

    def modified(self):
        return self.__meta[u'is_dir']

    def children(self):
        files = set()
        if self.__meta[u'is_dir']:
            for cmeta in self.__meta[u'children']:
                path = cmeta[u'path']
                files.add(path)
        else:
            raise LoxApiError('Not a directory')
        return files

    def hash(self):
        return self.__meta[u'hash']

class LoxCache(FileInfo):

    def __init__(self,Session,Dir):
        pass
