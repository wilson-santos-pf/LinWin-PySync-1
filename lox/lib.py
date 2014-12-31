'''
Module with auxiliary functions
'''

import os
import binascii
from datetime import datetime
import iso8601


def to_timestamp(self, dt, epoch=datetime(1970,1,1,tzinfo=iso8601.UTC)):
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 1e6 

def get_conflict_name(self,original):
    base,ext = os.path.splitext(original)
    x0 = os.urandom(3)
    x1 = binascii.hexlify(x0)
    # TODO: check if file exists and loop generating random extension until no conflict
    new_name =  base + "_conflict_" + x1 + ext
    return new_name

