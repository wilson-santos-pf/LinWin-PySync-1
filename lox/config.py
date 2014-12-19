'''
Description:

    Module for lox-client configuration. Not a class so not needed to instantiate
    throughout the application. Globally loads clinet configuration.

Usage:

    import config
    
    config.session('localhost')['user']

Todo:

    Add change of configuration and save() function    

'''

import sys
import os
import ConfigParser

def load():
    global __config
    conf_dir = os.environ['HOME']+'/.lox'
    if not os.path.isdir(conf_dir):
        os.mkdir(conf_dir)
    if not os.path.isfile(conf_dir+"/lox-client.conf"):
        f = open(conf_dir+"/lox-client.conf",'w+')
        f.write(";empty config file")
        f.write(os.linesep)
        f.close()
    path = os.environ['HOME']+'/.lox/lox-client.conf'
    __config = ConfigParser.RawConfigParser()
    __config.read(path)
    
def sessions():
    global __config
    return __config.sections()

def session(Session):
    global __config
    d = dict()
    for key,value in __config.items(Session):
        d[key] = value
    return d

load()

