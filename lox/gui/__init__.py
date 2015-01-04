'''
'''
import os

if not (os.getenv('DISPLAY') is None):
    from gnome import *
else:
    from null import *
