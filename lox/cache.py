'''
Module levert een eenvoudige cahce gebaseerd op shelve

Usage:
    s = LoxCache("filename")
    s["key"] = "valus" # automatically does sync()
    del s["key"] # okay even ik key does not exist

'''

from shelve import DbfilenameShelf

class LoxCache(DbfilenameShelf):
    
    # default to newer pickle protocol and writeback=True
    def __init__(self, filename, protocol=2, writeback=True):
        DbfilenameShelf.__init__(self, filename, protocol=protocol, writeback=writeback)
    
    def __setitem__(self, name, value):
        key = name.encode('utf8')
        DbfilenameShelf.__setitem__(self, key, value)
        self.sync()
    
    def __delitem__(self, name):
        key = name.encode('utf8')
        if DbfilenameShelf.has_key(self,key):
            DbfilenameShelf.__delitem__(self, key)
            self.sync()

