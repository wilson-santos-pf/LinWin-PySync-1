'''

Module for logging sessions

Usage: create an instance per session

'''
import os
from datetime import datetime

class LoxLogger:

    (NONE,ERROR,WARN,INFO,DEBUG) = (0,1,2,3,4)

    def __init__(self,Name):
        self.__log_file = os.environ['HOME']+'/.lox/.'+Name+'.log'
        self.__log_handle = open(self.__log_file,'a')
        self.__log_level = self.DEBUG # WARN?

    def __del__(self):
        self.__log_handle.close()

    def __log(self,Level,Msg):
        dt = datetime.now()
        self.__log_handle.write("%s-%s-%s %s:%s:%s - " % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
        self.__log_handle.write("[%s] " % Level)
        self.__log_handle.write(Msg)
        self.__log_handle.write(os.linesep)
        print(Msg)

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


