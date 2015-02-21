'''

Module that defines a class for a
synchronization session per account

Usage:

    import lox.config
    from lox.session import LoxSession

    for Name in lox.config.settings.iterkeys()
        S = LoxSession(Name)

'''
import os
import mimetypes
import time
import threading
import traceback
from datetime import datetime
import iso8601
from collections import deque

import lox.config
import lox.lib
from lox.api import LoxApi
from lox.logger import LoxLogger
from lox.error import LoxError, LoxFatal
from lox.cache import LoxCache

class FileInfo:
    '''
    Simple class used as record/struct of file info
    '''
    isdir = None
    modified = None
    size = None
    hash = None
    encrypted = None


class LoxSession(threading.Thread):
    '''
    Class that definess the session to synchronize a local folder with a LocalBox store
    '''

    def __init__(self,Name):
        '''
        Initialize the session
        '''
        super(LoxSession,self).__init__()
        self.daemon = True
        self.name = Name
        local_dir = lox.config.settings[Name]['local_dir']
        self._root = os.path.expanduser(local_dir)
        if not os.path.isdir(self._root):
            os.mkdir(self._root)
        self._logger = LoxLogger(Name)
        self._cache = LoxCache(Name, self._logger)
        self._api = LoxApi(Name)
        self._queue = deque()
        self.interval = float(lox.config.settings[Name]['interval'])
        if self.interval<60 and self.interval>0:
            self._logger.warn("Interval is {0} seconds, this is short".format(self.interval))
        self._stop_request = threading.Event()
        self.last_error = "none"
        self.status = "initialized"
        self._logger.info("Session loaded")

    def stop(self):
        '''
        Stop a session, for now it completes a sync first
        '''
        if self.is_alive():
            self._stop_request.set()
            self.join()

    def run(self):
        '''
        Running the session as a thread
        '''
        self.status = "session started"
        self._logger.info("Session started")
        self._stop_request.wait(1) # needed to get GUI started first?
        while not self._stop_request.is_set():
            try:
                self.sync()
            except (IOError, LoxError) as e:
                # IOError means not online, report and continue
                self._logger.error(str(e))
            except (LoxFatal) as e:
                # LoxFatal means a fatal error, report this and abort session
                self._logger.error(str(e))
                break
            except Exception as e:
                self._logger.critical("Exception in sync\n{0}".format(traceback.format_exc()))
            if self.interval>0:
                self.status = 'waiting  since {:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
                self._logger.info("Session waiting for next sync")
                self._stop_request.wait(self.interval)
            else:
                break
        self._logger.info("Session stopped")
        # cleanup everything nicely
        del self._cache
        del self._api
        del self._queue
        del self._logger

    def sync(self, path='/'):
        '''
        Synchronize given path start worker thread to handle queue
        and fills queue with renconciliation of directories
        '''
        self.status = 'sync running since {:%Y-%m-%d %H:%M:%S}'.format(datetime.now())
        self._logger.info("Sync started")
        self._reconcile(path)
        while not self._stop_request.is_set():
            try:
                filename = self._queue.popleft()
                local = self._file_info_local(filename)
                remote = self._file_info_remote(filename)
                cached = self._file_info_cache(filename)
                action = self._resolve(local,remote,cached)
                self._logger.debug("Resolving '{0}' leads to {1}".format(filename,action.__name__[1:]))
                action(filename)
            except IndexError:
                self._logger.info("Sync completed")
                break

    def _reconcile(self,path):
        '''
        Gets directory contents both local and remote, reconciles these sets
        and puts the items in the worker queue
        '''
        self._logger.debug("Reconcile '{0}'".format(path))
        # fetch local directory
        local_files = set()
        local_dir = self._root+path
        if os.path.isdir(local_dir):
            for item in os.listdir(local_dir):
                filename = os.path.join(path,item)
                local_files.add(filename)
        else:
            raise LoxError('Not a directory (local)')
        # fetch remote directory
        remote_files = set()
        meta = self._api.meta(path)
        if meta[u'is_dir']:
            if u'children' in meta:
                for child_meta in meta[u'children']:
                    child_path = child_meta[u'path']
                    remote_files.add(child_path)
        else:
            raise LoxError('Not a directory (remote)')
        # reconcile
        files = local_files | remote_files
        for f in files:
            #self._logger.debug("Added to queue '%s'" % f)
            self._queue.append(f)

    def _resolve(self,Local,Remote,Cached):
        '''
        Piece de resistance: resolve what to do with a file
        '''
        #print "    [DEBUG] local:  ",Local.isdir,Local.modified,Local.size
        #print "    [DEBUG] remote: ",Remote.isdir,Remote.modified,Remote.size
        #print "    [DEBUG] cached: ",Cached.isdir,Cached.modified,Cached.size
        '''
        Original rules from Erlang code are given as comment
        FileInfo is always given so 'FileInfo unknown' is uniformly translated with 'FileInfo.size is None'
        '''
        #resolve({file   ,Modified ,Size },{file   ,Modified ,Size },{file   ,Modified ,Size }) -> same;
        if (Local.isdir==Remote.isdir==Cached.isdir and
                Local.modified==Remote.modified==Cached.modified and
                Local.size==Remote.size==Cached.size):
            return self._same
        #resolve({dir    ,_        ,_    },{dir    ,_        ,_    },{dir    ,_        ,_    }) -> walk_dir;
        if (Local.isdir and Remote.isdir and Cached.isdir):
            return self._walk
        #resolve({dir    ,_        ,_    },{dir    ,_        ,_    },unknown                  ) -> update_and_walk;
        if (Local.isdir and Remote.isdir and Cached.size is None):
            return self._update_and_walk
        #resolve(unknown                  ,{_Type  ,_Modified,_Size},unknown                  ) -> download;
        if (Local.size is None and not (Remote.size is None) and Cached.size is None):
            return self._download
        #resolve({_Type  ,_Modified,_Size},unknown                  ,unknown                  ) -> upload;
        if (not (Local.size is None) and Remote.size is None and Cached.size is None):
            return self._upload
        #resolve({file   ,Modified ,Size },{file   ,Modified ,Size },unknown                  ) -> update_cache;
        if (Local.isdir==Remote.isdir==False and
                Local.modified==Remote.modified and
                Cached.size is None):
            return self._update_cache
        #resolve({file   ,ModifiedL,SizeL},{file   ,ModifiedR,SizeR},unknown                  ) when ModifiedL /= ModifiedR -> conflict;
        if (Local.isdir==Remote.isdir==False and
                Local.modified!=Remote.modified and
                Cached.size is None):
            return self._conflict
        #resolve({file   ,ModifiedL,SizeL},{file   ,ModifiedR,_    },{file   ,ModifiedL,SizeL}) when ModifiedR > ModifiedL -> download;
        if (Local.isdir==Remote.isdir==Cached.isdir==False and
                Local.modified < Remote.modified and
                Local.modified == Cached.modified and
                Local.size == Cached.size):
            return self._download
        #resolve({file   ,ModifiedL,_    },{file   ,ModifiedR,SizeR},{file   ,ModifiedR,SizeR}) when ModifiedL > ModifiedR -> upload;
        if (Local.isdir==Remote.isdir==Cached.isdir==False and
                Local.modified > Remote.modified and
                Remote.modified == Cached.modified and
                Remote.size == Cached.size):
            return self._download
        #resolve({file   ,Modified ,Size },unknown                  ,{file   ,Modified ,Size }) -> delete_local;
        if (Local.isdir==Cached.isdir==False and
                Remote.size is None and
                Local.modified == Cached.modified and
                Local.size == Cached.size):
            return self._delete_local
        #resolve(unknown                  ,{file   ,Modified ,Size },{file   ,Modified ,Size }) -> delete_remote;
        if (Remote.isdir==Cached.isdir==False and
                Local.size is None and
                Remote.modified == Cached.modified and
                Remote.size == Cached.size):
            return self._delete_remote
        #resolve({dir    ,_        ,_    },unknown                  ,{dir    ,_        ,_    }) -> delete_local;
        if (Local.isdir==Cached.isdir==True
                and Remote.size is None):
            return self._delete_local
        #resolve(unknown                  ,{dir    ,_        ,_    },{dir    ,_        ,_    }) -> delete_remote;
        if (Remote.isdir==Cached.isdir==True and
                Local.size is None):
            return self._delete_remote
        #resolve({file   ,_        ,_    },{dir    ,_        ,_    },{_      ,_        ,_    }) -> conflict;
        #resolve({dir    ,_        ,_    },{file   ,_        ,_    },{_      ,_        ,_    }) -> conflict;
        if (Local.isdir != Remote.isdir):
            return self._conflict
        #resolve(unknown                  ,unknown                  ,unknown                  ) -> strange;
        if (Local.size is None and Remote.size is None and Cached.size is None):
            return self.strange
        #resolve(_OtherL                  ,_OtherR                  ,_OtherC                  ) -> not_resolved.
        return self._not_resolved

    def _file_info_local(self,path):
        '''
        Get meta data from local file:
        (1) isdir
        (2) mtime (as DateTime object)
        (3) size (in case of directory the number of files)
        '''
        fullpath = self._root+path
        f = FileInfo()
        if os.path.exists(fullpath):
            f.isdir = os.path.isdir(fullpath)
            mtime = os.path.getmtime(fullpath)
            m = datetime.utcfromtimestamp(mtime)
            # normalize the date with a timezone and omit microseconds (UGLY)
            f.modified = datetime(m.year,m.month,m.day,m.hour,m.minute,m.second,tzinfo=iso8601.UTC)
            if f.isdir:
                files = os.listdir(fullpath)
                f.size = len(files)
            else:
                f.size = os.path.getsize(fullpath)
        return f

    def _file_info_remote(self,path):
        '''
        Get meta data from remote file:
        (1) isdir
        (2) mtime (as DateTime object)
        (3) size (in case of directory the number of files)
        '''
        f = FileInfo()
        meta = self._api.meta(path)
        if not (meta is None):
            f.isdir = meta[u'is_dir']
            modified_at = meta[u'modified_at']
            f.modified = iso8601.parse_date(modified_at)
            if f.isdir:
                if u'children' in meta:
                    files = meta[u'children']
                    f.size = len(files)
                else:
                    f.size = 0
            else:
                f.size = meta[u'size']
        return f

    def _file_info_cache(self,path):
        '''
        Get meta data from cache
        '''
        key = path.encode('utf8')
        file_info = self._cache.get(key,FileInfo())
        return file_info

    # actions
    def _same(self,path):
        '''
        File is synchronized, nothing to do
        '''
        pass

    def _walk(self,path):
        '''
        Recursively walk directory
        '''
        self._reconcile(path)

    def _update_cache(self,path):
        '''
        Update the cache
        '''
        file_info = self._file_info_local(path)
        self._cache[path] = file_info

    def _update_and_walk(self,path):
        '''
        Update the cache and recursively walk directory
        '''
        file_info = self._file_info_local(path)
        self._cache[path] = file_info
        self._reconcile(path)

    def _download(self,path):
        '''
        Download the file, apply server meta data
        (1) Download the local file from the server (via temp file)
        (2) Get the meta data from server
        (3) Override local meta data and update cache
        '''
        self._logger.info("Download %s" % path)
        meta = self._api.meta(path)
        if not (meta is None):
            filename = self._root+path
            if meta[u'is_dir']:
                os.mkdir(filename)
                self._reconcile(path)
            else:
                contents = self._api.download(path)
                # use temp file in case large downloads get interrupted
                dl_name = lox.lib.get_dl_name(filename)
                f = open(dl_name,'wb')
                f.write(contents)
                f.close()
                os.rename(dl_name,filename)
                modified_at = meta[u'modified_at']
                modified = iso8601.parse_date(modified_at)
                mtime = lox.lib.to_timestamp(modified)
                os.utime(filename,(os.path.getatime(filename),mtime))
                # update cache
                file_info = FileInfo()
                file_info.isdir = False
                file_info.modified = modified
                file_info.size = os.path.getsize(filename)
                self._cache[path] = file_info

    def _upload(self,path):
        '''
        Upload the file, apply server neta data local:
        (1) Send the file to th server
        (2) Retrieve what meta data the server gave to the file
        (3) Use this meta data to update local file info and cache
        '''
        self._logger.info("Upload %s" % path)
        local_dir = self._root+path
        if os.path.isdir(local_dir):
            self._api.create_folder(path)
            file_info = self._file_info_local(path)
            self._cache[path] = file_info
            self._reconcile(path)
        else:
            # (1) file timestamp must be same as on server after upload, can this be done more efficient?
            content_type,encoding = mimetypes.guess_type(path)
            filename = self._root+path
            f = open(filename,'rb')
            contents = f.read()
            f.close()
            self._api.upload(path,content_type,contents)
            # file timestamp must be same as on server:
            # (1) can this be done more efficient?
            # (2) put in separate function _touch()?
            meta = self._api.meta(path)
            modified_at = meta[u'modified_at']
            modified = iso8601.parse_date(modified_at)
            mtime = lox.lib.to_timestamp(modified)
            os.utime(filename,(os.path.getatime(filename),mtime))
            # update cache
            file_info = FileInfo()
            file_info.isdir = False
            file_info.modified = modified
            file_info.size = os.path.getsize(filename)
            self._cache[path] = file_info

    def _delete_local(self,path):
        '''
        Delete the local file or directory (recursively)
        '''
        self._logger.debug("Delete (local) %s" % path)
        full_path = self._root+path
        if os.path.isdir(full_path):
            for item in os.listdir(full_path):
                filename = os.path.join(path,item)
                self._delete_local(filename)
            os.rmdir(full_path)
            del self._cache[path]
        else:
            os.remove(full_path)
            del self._cache[path]

    def _delete_remote(self,path):
        '''
        Delete the remote file or directory (recursively)
        '''
        self._logger.debug("Delete (remote) %s" % path)
        meta = self._api.meta(path)
        if not (meta is None):
            if meta[u'is_dir']:
                if u'children' in meta:
                    for child_meta in meta[u'children']:
                        child_path = child_meta[u'path']
                        self._delete_remote(child_path)
            self._api.delete(path)
            del self._cache[path]


    def _conflict(self,path):
        '''
        Handle a conflicting situation, the server always wins:
        (1) Local file is renamed
        (2) Remote file is downloaded
        '''
        # (1) rename local with .conflict_nnnn extension
        full_path = self._root+path
        conflict_path = lox.lib.get_conflict_name(path)
        new_name =  self._root+conflict_path
        self._logger.info("Renamed (local) {0} to {1}".format(path,conflict_path))
        os.rename(full_path,new_name)
        # (2) download remote to tmp/unique file (like maildir)
        self._download(path)
        self._upload(conflict_path)

    def _strange(self,path):
        '''
        This situation should not occur
        '''
        self._logger.error("Resolving '{0}' led to strange situation".format(path))

    def _not_resolved(self,path):
        '''
        Somehow this situation is not yet handled
        '''
        self._logger.error("Path '{0}' could not be resolved".format(path))

