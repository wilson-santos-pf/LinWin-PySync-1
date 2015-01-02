'''

Module that controls synchronization session per account

Usage:

    import lox.config
    from lox.session import LoxSession
    
    for Name in lox.config.settings.iterkeys()
        S = LoxSession(Name)

'''
import os
import mimetypes
import time
from threading import Thread
import Queue
import traceback
from datetime import datetime
import iso8601

import lox.config
import lox.lib
from lox.api import LoxApi
from lox.logger import LoxLogger
from lox.error import LoxError
from lox.cache import LoxCache

class FileInfo:
    '''
    Simple class used as record/struct of file info
    '''
    isdir = None
    modified = None
    size = None



class LoxSession(Thread):
    '''
    Class that definess the session to synchronize a local folder with a LocalBox store
    '''

    def __init__(self,Name, interactive = False):
        Thread.__init__(self)
        self.name = Name
        cache_name = os.environ['HOME']+'/.lox/.'+Name+'.cache'
        self.__cache = LoxCache(cache_name)
        local_dir = lox.config.settings[Name]['local_dir']
        self.root = os.path.expanduser(local_dir)
        if not os.path.isdir(self.root):
            os.mkdir(self.root)
        self.logger = LoxLogger(Name, interactive)
        self.api = LoxApi(Name)
        self.queue = Queue.Queue()
        if not interactive:
            self.interval = float(lox.config.settings[Name]['interval'])
        else:
            self.interval = 0
        if self.interval<60 and self.interval>0:
            self.logger.warn("Interval is {0} seconds, this is short".format(self.interval))
        self.running = True
        self.status = "initialized"
        self.logger.info("Session started")

    def __del__(self):
        self.logger.info("Session stopped")


    def status(self):
        return self.status

    def run(self):
        self.status = "started"
        while self.running:
            try:
                self.status = "running sync"
                self.sync()
            except Exception as e:
                self.logger.error("Sync aborted for reason: "+str(e))
                traceback.print_exc(file=self.logger.handle)
            if self.interval>0:
                self.status = "waiting"
                time.sleep(self.interval)
            else:
                self.status = "stopped"
                break

    def sync(self,Path='/'):
        self.reconcile(Path)
        Worker = Thread(target=self._sync_worker)
        Worker.daemon = True
        Worker.start()
        self.queue.join()
        
    def _sync_worker(self):
        while True:
            path = self.queue.get()
            try:
                local = self.file_info_local(path)
                remote = self.file_info_remote(path)
                cached = self.file_info_cache(path)
                action = self.resolve(local,remote,cached)
                self.logger.info("Resolving '%s' leads to %s" %(path,action.__name__))
                action(path)
            except Exception as e:
                traceback.print_exc(file=self.logger.handle)
            self.queue.task_done()
                
    def reconcile(self,path):
        self.logger.debug("Reconcile '{0}'".format(path))
        # fetch local directory
        local_files = set()
        local_dir = self.root+path
        if os.path.isdir(local_dir):
            for item in os.listdir(local_dir):
                filename = os.path.join(path,item)
                local_files.add(filename)
        else:
            raise LoxError('Not a directory (local)')
        # fetch remote directory
        remote_files = set()
        meta = self.api.meta(path)
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
            #self.logger.debug("Added to queue '%s'" % f)
            self.queue.put(f)

    def resolve(self,Local,Remote,Cached):
        '''
        Resolve what to do
        Original rules are given as comment
        FileInfo is always given so 'FileInfo unknown' is uniformly translated with 'FileInfo.size is None'
        '''
        #print "    [DEBUG] local:  ",Local.isdir,Local.modified,Local.size
        #print "    [DEBUG] remote: ",Remote.isdir,Remote.modified,Remote.size
        #print "    [DEBUG] cached: ",Cached.isdir,Cached.modified,Cached.size
        #-------------------
        #resolve({file   ,Modified ,Size },{file   ,Modified ,Size },{file   ,Modified ,Size }) -> same;
        if (Local.isdir==Remote.isdir==Cached.isdir and 
                Local.modified==Remote.modified==Cached.modified and 
                Local.size==Remote.size==Cached.size):
            return self.same
        #resolve({dir    ,_        ,_    },{dir    ,_        ,_    },{dir    ,_        ,_    }) -> walk_dir;
        if (Local.isdir and Remote.isdir and Cached.isdir):
            return self.walk
        #resolve({dir    ,_        ,_    },{dir    ,_        ,_    },unknown                  ) -> update_and_walk;
        if (Local.isdir and Remote.isdir and Cached.size is None):
            return self.update_and_walk
        #resolve(unknown                  ,{_Type  ,_Modified,_Size},unknown                  ) -> download;
        if (Local.size is None and not (Remote.size is None) and Cached.size is None):
            return self.download
        #resolve({_Type  ,_Modified,_Size},unknown                  ,unknown                  ) -> upload;
        if (not (Local.size is None) and Remote.size is None and Cached.size is None):
            return self.upload
        #resolve({file   ,Modified ,Size },{file   ,Modified ,Size },unknown                  ) -> update_cache;
        if (Local.isdir==Remote.isdir==False and 
                Local.modified==Remote.modified and 
                Cached.size is None):
            return self.update_cache
        #resolve({file   ,ModifiedL,SizeL},{file   ,ModifiedR,_    },{file   ,ModifiedL,SizeL}) when ModifiedR > ModifiedL -> download;
        if (Local.isdir==Remote.isdir==Cached.isdir==False and 
                Local.modified < Remote.modified and 
                Local.modified == Cached.modified and 
                Local.size == Cached.size):
            return self.download
        #resolve({file   ,ModifiedL,_    },{file   ,ModifiedR,SizeR},{file   ,ModifiedR,SizeR}) when ModifiedL > ModifiedR -> upload;
        if (Local.isdir==Remote.isdir==Cached.isdir==False and 
                Local.modified > Remote.modified and 
                Remote.modified == Cached.modified and 
                Remote.size == Cached.size):
            return self.download
        #resolve({file   ,Modified ,Size },unknown                  ,{file   ,Modified ,Size }) -> delete_local;
        if (Local.isdir==Cached.isdir==False and
                Remote.size is None and
                Local.modified == Cached.modified and
                Local.size == Cached.size):
            return self.delete_local
        #resolve(unknown                  ,{file   ,Modified ,Size },{file   ,Modified ,Size }) -> delete_remote;
        if (Remote.isdir==Cached.isdir==False and
                Local.size is None and
                Remote.modified == Cached.modified and
                Remote.size == Cached.size):
            return self.delete_remote
        #resolve({dir    ,_        ,_    },unknown                  ,{dir    ,_        ,_    }) -> delete_local;
        if (Local.isdir==Cached.isdir==True 
                and Remote.size is None):
            return self.delete_local
        #resolve(unknown                  ,{dir    ,_        ,_    },{dir    ,_        ,_    }) -> delete_remote;
        if (Remote.isdir==Cached.isdir==True and
                Local.size is None):
            return self.delete_remote
        #resolve({file   ,_        ,_    },{dir    ,_        ,_    },{_      ,_        ,_    }) -> conflict;
        #resolve({dir    ,_        ,_    },{file   ,_        ,_    },{_      ,_        ,_    }) -> conflict;
        if (Local.isdir != Remote.isdir):
            return self.conflict
        #resolve(unknown                  ,unknown                  ,unknown                  ) -> strange;
        if (Local.size is None and Remote.size is None and Cached.size is None):
            return self.strange
        #resolve(_OtherL                  ,_OtherR                  ,_OtherC                  ) -> not_resolved.
        return self.not_resolved

    def file_info_local(self,path):
        fullpath = self.root+path
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

    def file_info_remote(self,path):
        f = FileInfo()
        meta = self.api.meta(path)
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

    def file_info_cache(self,path):
        key = path.encode('utf8')
        file_info = self.__cache.get(key,FileInfo())
        return file_info

    # actions
    def same(self,path):
        pass
    
    def walk(self,path):
        self.reconcile(path)
    
    def update_cache(self,path):
        file_info = self.file_info_local(path)
        self.__cache[path] = file_info

    def update_and_walk(self,path):
        file_info = self.file_info_local(path)
        self.__cache[path] = file_info
        self.reconcile(path)

    def download(self,path):
        self.logger.info("Download %s" % path)
        meta = self.api.meta(path)
        if not (meta is None):
            filename = self.root+path
            if meta[u'is_dir']:
                os.mkdir(filename)
                if u'children' in meta:
                    for child_meta in meta[u'children']:
                        child_path = child_meta[u'path']
                        # put in worker queue?
                        self.download(child_path)
            else:
                contents = self.api.download(path)
                f = open(filename,'wb')
                f.write(contents)
                f.close()
                modified_at = meta[u'modified_at']
                modified = iso8601.parse_date(modified_at)
                mtime = lox.lib.to_timestamp(modified)
                os.utime(filename,(os.path.getatime(filename),mtime))
                # update cache
                file_info = FileInfo()
                file_info.isdir = False
                file_info.modified = modified
                file_info.size = os.path.getsize(filename)
                self.__cache[path] = file_info
            
    def upload(self,path):
        self.logger.info("Upload %s" % path)
        local_dir = self.root+path
        if os.path.isdir(local_dir):
            self.api.create_folder(path)
            for item in os.listdir(local_dir):
                filename = os.path.join(path,item)
                self.upload(filename)
            file_info = self.file_info_local(path)
            self.__cache[path] = file_info
        else:
            # (1) file timestamp must be same as on server after upload, can this be done more efficient?
            content_type,encoding = mimetypes.guess_type(path)
            filename = self.root+path
            f = open(filename,'rb')
            contents = f.read()
            f.close()
            self.api.upload(path,content_type,contents)
            # file timestamp must be same as on server:
            # (1) can this be done more efficient?
            # (2) put in separate function _touch()?
            meta = self.api.meta(path)
            modified_at = meta[u'modified_at']
            modified = iso8601.parse_date(modified_at)
            mtime = self._totimestamp(modified)
            os.utime(filename,(os.path.getatime(filename),mtime))
            # update cache
            file_info = FileInfo()
            file_info.isdir = False
            file_info.modified = modified
            file_info.size = os.path.getsize(filename)
            self.__cache[path] = file_info

    def delete_local(self,path):
        self.logger.debug("Delete (local) %s" % path)
        full_path = self.root+path
        if os.path.isdir(full_path):
            for item in os.listdir(full_path):
                filename = os.path.join(path,item)
                self.delete_local(filename)
            os.rmdir(full_path)
            del self.__cache[path]
        else:
            os.remove(full_path)
            del self.__cache[path]
            
    def delete_remote(self,path):
        self.logger.debug("Delete (remote) %s" % path)
        meta = self.api.meta(path)
        if not (meta is None):
            if meta[u'is_dir']:
                if u'children' in meta:
                    for child_meta in meta[u'children']:
                        child_path = child_meta[u'path']
                        self.delete_remote(child_path)
            self.api.delete(path)
            del self.__cache[path]

            
    def conflict(self,path):
        # (1) rename local with .conflict_nnnn extension
        full_path = self.root+path
        base,ext = os.path.splitext(path)
        conflict_path = lox.lib.get_conflict_name(path)
        new_name =  self.root+conflict_path
        self.logger.info("Renamed (local) {0} to {1}".format(path,conflict_path))
        os.rename(full_path,new_name)
        # (2) download remote to tmp/unique file (like maildir)
        self.download(path)
        self.upload(conflict_path)
    
    def strange(self,path):
        self.logger.error("Resolving '{0}' led to strange situation".format(path))

    def not_resolved(self,path):
        self.logger.error("Path '{0}' could not be resolved".format(path))

