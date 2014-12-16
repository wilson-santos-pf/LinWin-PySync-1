'''

Module that controls synchronization session per account

Usage:

    import config
    from session import Session
    
    for Name in config.sessions()
        S = Session(Name)

'''
import os
import mimetypes
import time
from datetime import datetime
from threading import Thread
import shelve
import Queue
import traceback
import iso8601
import api
import logger
import config
from error import LoxError


class FileInfo:
    '''
    Simple class used as record/struct of file info
    '''
    isdir = None
    modified = None
    size = None



class Session(Thread):
    '''
    Class that definess the session to synchronize a local folder with a LocalBox store
    '''

    def __init__(self,Name):
        Thread.__init__(self)
        self.name = Name
        cache_name = os.environ['HOME']+'/.lox/.'+Name+'.cache'
        self._cache = shelve.open(cache_name)
        local_dir = config.session(Name)['local_dir']
        self.root = os.path.expanduser(local_dir)
        self.logger = logger.Logger(Name)
        self.api = api.Api(Name)
        self.queue = Queue.Queue()
        self.interval = float(config.session(Name)['interval'])
        self.running = True

    def run(self):
        while self.running:
            self.sync()
            time.sleep(self.interval)

    def sync(self,Path='/'):
        self.reconcile(Path)
        Worker = Thread(target=self._sync_worker)
        Worker.daemon = True
        Worker.start()
        #self.queue.join()
        
    def _sync_worker(self):
        while True:
            try:
                # get next item
                path = self.queue.get()
                # do work
                local = self.file_info_local(path)
                remote = self.file_info_remote(path)
                cached = self.file_info_cache(path)
                action = self.resolve(local,remote,cached)
                #self.logger.info("Resolving '"+path+" leads to "+action.__name__)
                print("Resolving '"+path+" leads to "+action.__name__)
                # do action
                action(path)
                # finalize
                self.queue.task_done()
            except Exception:
                traceback.print_exc()
                break
                
    def reconcile(self,path):
        print "Reconcile: ",path
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
            print "Add to queue: "+f
            self.queue.put(f)

    def resolve(self,local,remote,cached):
        '''
        Resolve what to do
        Original rules are given as comment
        FileInfo is always given so 'FileInfo unknown' is uniformly translated with 'FileInfo.size is None'
        '''
	#TODO: fix this up so it is actually readable
        Local = local
  	Remote = remote


        #print "    [DEBUG] local:  ",local.isdir,local.modified,local.size
        #print "    [DEBUG] remote: ",remote.isdir,remote.modified,remote.size
        #print "    [DEBUG] cached: ",cached.isdir,cached.modified,cached.size
        #-------------------
        #resolve({file   ,Modified ,Size },{file   ,Modified ,Size },{file   ,Modified ,Size }) -> same;
        if (local.isdir==remote.isdir==cached.isdir and 
                local.modified==remote.modified==cached.modified and 
                local.size==remote.size==cached.size):
            return self.same
        #resolve({dir    ,_        ,_    },{dir    ,_        ,_    },{dir    ,_        ,_    }) -> walk_dir;
        if (local.isdir and remote.isdir and cached.isdir):
            return self.walk
        #resolve({dir    ,_        ,_    },{dir    ,_        ,_    },unknown                  ) -> update_and_walk;
        if (local.isdir and remote.isdir and cached.size is None):
            return self.update_and_walk
        #resolve(unknown                  ,{_Type  ,_Modified,_Size},unknown                  ) -> download;
        if (local.size is None and not (remote.size is None) and cached.size is None):
            return self.download
        #resolve({_Type  ,_Modified,_Size},unknown                  ,unknown                  ) -> upload;
        if (not (local.size is None) and remote.size is None and cached.size is None):
            return self.upload
        #resolve({file   ,Modified ,Size },{file   ,Modified ,Size },unknown                  ) -> update_cache;
        if (local.isdir==remote.isdir==False and 
                local.modified==remote.modified and 
                cached.size is None):
            return self.update_cache
        #resolve({file   ,ModifiedL,SizeL},{file   ,ModifiedR,_    },{file   ,ModifiedL,SizeL}) when ModifiedR > ModifiedL -> download;
        if (local.isdir==remote.isdir==cached.isdir==False and 
                local.modified < remote.modified and 
                local.modified == cached.modified and 
                local.size == cached.size):
            return self.download
        #resolve({file   ,ModifiedL,_    },{file   ,ModifiedR,SizeR},{file   ,ModifiedR,SizeR}) when ModifiedL > ModifiedR -> upload;
        if (local.isdir==remote.isdir==cached.isdir==False and 
                local.modified > remote.modified and 
                remote.modified == cached.modified and 
                remote.size == cached.size):
            return self.download
        #resolve({file   ,Modified ,Size },unknown                  ,{file   ,Modified ,Size }) -> delete_local;
        if (local.isdir==cached.isdir==False and
                Remote is None and
                local.modified == cached.modified and
                local.size == cached.size):
            return self.delete_local
        #resolve(unknown                  ,{file   ,Modified ,Size },{file   ,Modified ,Size }) -> delete_remote;
        if (remote.isdir==cached.isdir==False and
                Local is None and
                remote.modified == cached.modified and
                remote.size == cached.size):
            return self.delete_remote
        #resolve({dir    ,_        ,_    },unknown                  ,{dir    ,_        ,_    }) -> delete_local;
        if (local.isdir==cached.isdir==True 
                and Remote is None):
            return self.delete_local
        #resolve(unknown                  ,{dir    ,_        ,_    },{dir    ,_        ,_    }) -> delete_remote;
        if (remote.isdir==cached.isdir==False and
                Local is None):
            return self.delete_remote
        #resolve({file   ,_        ,_    },{dir    ,_        ,_    },{_      ,_        ,_    }) -> conflict;
        #resolve({dir    ,_        ,_    },{file   ,_        ,_    },{_      ,_        ,_    }) -> conflict;
        if (local.isdir != remote.isdir):
            return self.conflict
        #resolve(unknown                  ,unknown                  ,unknown                  ) -> strange;
        if (local.size is None and remote.size is None and cached.size is None):
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
        file_info = self._cache.get(key,FileInfo())
        print "READ: ",key,file_info.isdir,file_info.modified,file_info.size
        return file_info

    # actions
    def same(self,path):
        pass
    
    def walk(self,path):
        self.reconcile(path)
    
    def update_cache(self,path):
        # hangt op een of andere mannier
        key = path.encode('utf8')
        file_info = self.file_info_local(path)
        print "UPDATE: ",key,file_info.isdir,file_info.modified,file_info.size
        self._cache[key] = file_info

    def update_and_walk(self,path):
        file_info = self.file_info_local(path)
        self._cache['path'] = file_info
        self.reconcile(path)

    def download(self,path):
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
                # make safe download
                # (1) do not load file in memory
                # (2) using tmp dir and unique file and 
                # (3) then static link, just like in maildir
                contents = self.api.download(path)
                f = open(filename,'wb')
                f.write(contents)
                f.close()
                # file timestamp must be same as on server:
                # (1) can this be done more efficient?
                # (2) put in separate _function
                modified_at = meta[u'modified_at']
                modified = iso8601.parse_date(modified_at)
                mtime = self._totimestamp(modified)
                os.utime(filename,(os.path.getatime(filename),mtime))
                # update cache
                key = path.encode('utf8')
                file_info = FileInfo()
                file_info.isdir = False
                file_info.modified = modified
                file_info.size = os.path.getsize(filename)
                self._cache[key] = file_info
    
    def upload(self,path):
        local_dir = self.root+path
        if os.path.isdir(local_dir):
            self.api.create_folder(path)
            for item in os.listdir(local_dir):
                filename = os.path.join(path,item)
                self.upload(filename)
        else:
            # (1) file timestamp must be same as on server after upload, can this be done more efficient?
            content_type,encoding = mimetypes.guess_type(path)
            filename = self.root+path
            f = open(filename,'br')
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
            key = path.encode('utf8')
            file_info = FileInfo()
            file_info.isdir = False
            file_info.modified = modified
            file_info.size = os.path.getsize(filename)
            self._cache[key] = file_info

    def delete_local(sef,path):
        # (1) delete recursive locally
        # (2) delete recursive from cache
        pass
    
    def delete_remote(self,path):
        # (1) delete recursive from server
        #self.api.delete(path) is already recursive, but better depth first recursive delete?
        # (2) delete recursive from cache
        pass
    
    def conflict(self,path):
        # (1) download remote to tmp/unique file (like maildir) 
        # (2) rename local with .conflict_nnnn extension
        # (3) hard link to tmp with orignal filename
        # (4) delete tmp/unique
        pass
    
    def strange(self,path):
        self.logger.error("Resolving "+path+" led to strange situation")

    def not_resolved(self,path):
        self.logger.error(path+" could not be resolved")

    # internals
    # move this conversion functio to a library?
    
    def _totimestamp(self,dt, epoch=datetime(1970,1,1,tzinfo=iso8601.UTC)):
        td = dt - epoch
        # return td.total_seconds()
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 1e6 
