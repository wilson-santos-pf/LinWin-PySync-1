from functools import wraps
from logging import getLogger
from time import time


def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time()
        func(*args, **kwargs)
        getLogger(__name__).debug(func.__name__ + ' took: ' + str(time() - t) + ' seconds')

    return wrapper
