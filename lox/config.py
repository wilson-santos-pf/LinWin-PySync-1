'''
Description:

    Module for lox-client configuration. Not a class so not needed to instantiate
    throughout the application. Globally loads clinet configuration.

Usage:

    import config
    
    config.session('localhost')['user']
    config.get('localhost','user')

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
    __config.read(path)
    
def save():
    global __config
    conf_dir = os.environ['HOME']+'/.lox'
    if not os.path.isdir(conf_dir):
        os.mkdir(conf_dir)
    path = os.environ['HOME']+'/.lox/lox-client.conf'
    with open(path, 'wb') as f:
        __config.write(f)

def delete(Session):
    global __config
    __config.remove_section(Session)
    
def sessions():
    global __config
    return __config.sections()

def session(Session):
    global __config
    d = dict()
    for key,value in __config.items(Session):
        d[key] = value
    return d

def get(Session,Item,Value):
    global __config
    __config.get(Session,Item)

def set(Session,Item,Value):
    global __config
    __config.set(Session,Item,Value)


__config = ConfigParser.RawConfigParser()
load()

