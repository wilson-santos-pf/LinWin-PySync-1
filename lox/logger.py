'''

Module for logging sessions

Usage: create an instance per session

'''
import os

class Logger:

    (NONE,ERROR,WARN,INFO,DEBUG) = (0,1,2,3,4)

    def __init__(self,Name):
        self.__log_file = os.environ['HOME']+'/.lox/.'+Name+'.log'
        self.__log_handle = open(self.__log_file,'a')
        self.__log_level = self.WARN

    def __del__(self):
        self.__log_handle.close()

    def __log(self,Msg):
        self.__log_handle.write(Msg)
        print(Msg)

    def set_level(self,level):
        self.__log_level = level
        
    def error(self,Msg):
        if self.__log_level>=self.ERROR:
            self.__log(Msg)

    def warn(self,Msg):
        if self.__log_level>=self.WARN:
            self.__log(Msg)

    def info(self,Msg):
        if self.__log_level>=self.INFO:
            self.__log(Msg)

    def debug(self,Msg):
        if self.__log_level>=self.DEBUG:
            self.__log(Msg)


