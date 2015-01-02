'''

Module for logging sessions

Usage: create an instance per session

'''
import os
from datetime import datetime

class LoxLogger:

    (NONE,ERROR,WARN,INFO,DEBUG) = (0,1,2,3,4)

    def __init__(self,Name, Interactive):
        self.__log_file = os.environ['HOME']+'/.lox/.'+Name+'.log'
        self.handle = open(self.__log_file,'a')
        self.__log_level = self.DEBUG # WARN?
        self.__interactive = Interactive

    def __del__(self):
        self.handle.close()

    def __log(self,Level,Msg):
        if self.__interactive:
            print(Msg)
        else:
            dt = datetime.now()
            self.handle.write('{:%Y-%m-%d %H:%M:%S}'.format(dt))
            self.handle.write(' - [{0}] '.format(Level))
            self.handle.write(Msg)
            self.handle.write(os.linesep)

    def set_level(self,level):
        self.__log_level = level
        
    def error(self,Msg):
        if self.__log_level>=self.ERROR:
            self.__log("ERROR",Msg)

    def warn(self,Msg):
        if self.__log_level>=self.WARN:
            self.__log("WARN",Msg)

    def info(self,Msg):
        if self.__log_level>=self.INFO:
            self.__log("INFO",Msg)

    def debug(self,Msg):
        if self.__log_level>=self.DEBUG:
            self.__log("DEBUG",Msg)


