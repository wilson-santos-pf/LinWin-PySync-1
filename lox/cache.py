import os
import shelve


class LoxCache:

    def __init__(self,name):
        self.__file = os.environ['HOME']+'/.lox/'+name+'.cache'
        self.__dict = shelve.open(self.__file)

    def add_dir(self,Dir):
        if Dir == "/":
            s = self.__dict.get(Dir,set())
            self.__dict[Dir] = s
        else:
            Parent,This = os.path.split
            self.add_dir(Parent)
            self.__dict[Dir] = set()
        
        #self.__dict.sync()

    def list_dir(self,Dir):
        return self.__dict[Dir]

    def del_dir(self,Dir):
        self.__dict.pop(Dir,default = None)
        #self.__dict.sync()

    def add_file(self,Filename,Size,Modified):
        File = os.path.basename(Filename)
        Dir = os.path.dirname(Filename)
        self.add_dir(Dir)
        s = self.__dict.get(Dir)
        s.add(File)
        self.__dict[Dir] = s
        self.__dict[Filename] = (Size,Modified)
        #self.__dict.sync()

    def get_file(self,Filename):
        return self.__dict.get(Filename,None)
        
    def del_file(self,Filename):
        File = os.path.basename(Filename)
        Dir = os.path.dirname(Filename)
        s = self.__dict[Dir]
        s.discard(File) # raises KeyError
        self.__dict[Dir] = s
        self.__dict.pop(Filename,default = None)
        #self.__dict.sync()
        
        
    def __del__(self):
        self.__dict.close()



l = LoxCache("test")
l.add_file("/a/b",23,25)
l.add_file("/a/c",24,26)
l.add_file("/a/d",25,27)
l.add_file("/x/y/z",18,19)
print l.list_dir("/a")
# print l.list_dir("/")

path = "/a/b/c/d/"
folders=[]
while 1:
    path,folder=os.path.split(path)
    if folder!="":
        folders = [folder]+folders
    else:
        if path!="":
            folders = [path] + folders
        break

print folders
