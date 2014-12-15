'''
Description:

    Module for lox-client configuration. Not a class so not needed to instantiate
    throughout the application. Globally loads clinet configuration.

Usage:

    import lox.config
    
    lox.config.session('localhost')['user']

Todo:

    Add change of configuration and save() function    

'''

import sys
import os
import ConfigParser

def load():
    global __config
    conf_dir = os.environ['HOME']+'/.lox'
    try:
        os.mkdir(conf_dir)
    except OSError:
        pass
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

