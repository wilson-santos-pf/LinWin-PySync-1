'''
Description:

    Module for lox-client configuration. Not a class so not needed to
    instantiate throughout the application. Globally loads or saves the client
    configuration with the load() and save() functions. The configuration
    can be accessed as a dict of session settings through the variable named
    settings. Each session entry in the dict is again a dict of name/value
    pairs. At both levels all dict oprations apply.

Usage:

    import config

    config.load()
    user = config.settings['localhost']['username']
    config.settings['localhost']['username'] = 'newuser'
    config.save()

Todo:

    Add change of configuration and save() function

'''

import sys
import os
import ConfigParser

from lox.error import LoxError


def load():
    '''
    Load the config file as the current settings
    '''
    global settings
    settings = dict()
    conf_dir = os.environ['HOME']+'/.lox'
    if not os.path.isdir(conf_dir):
        os.mkdir(conf_dir)
    if not os.path.isfile(conf_dir+"/lox-client.conf"):
        f = open(conf_dir+"/lox-client.conf",'w+')
        f.write(";empty config file")
        f.write(os.linesep)
        f.close()
    path = os.environ['HOME']+'/.lox/lox-client.conf'
    config = ConfigParser.RawConfigParser()
    config.read(path)
    for session in config.sections():
        settings[session] = dict()
        for key,value in config.items(session):
            settings[session][key] = value

def save():
    '''
    Load the current settings to the config file
    '''
    global settings
    conf_dir = os.environ['HOME']+'/.lox'
    if not os.path.isdir(conf_dir):
        os.mkdir(conf_dir)
    path = os.environ['HOME']+'/.lox/lox-client.conf'
    config = ConfigParser.RawConfigParser()
    for session,d in settings.iteritems():
        config.add_section(session)
        for item,value in d.iteritems():
            config.set(session,item,value)
    f = open(path, 'wb')
    config.write(f)
    f.close()

def check(name, items=[]):
    '''
    Check is the list of proprties is defined for the section given by name
    '''
    global settings
    for prop in items:
        if not (prop in settings[name]):
            return False
    return True


settings = dict()
load()

