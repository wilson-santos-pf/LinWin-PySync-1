#!/usr/bin/python

from datetime import tzinfo, timedelta

class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta(0)

    def __repr__(self):
        return "<FixedOffset %r %r>" % (self.__name, self.__offset)


utc = FixedOffset(0, "UTC")
