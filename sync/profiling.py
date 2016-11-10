from time import sleep, time
from functools import wraps


def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time()
        func(*args, **kwargs)
        print func.__name__, 'took:', time() - t, 'seconds'

    return wrapper
