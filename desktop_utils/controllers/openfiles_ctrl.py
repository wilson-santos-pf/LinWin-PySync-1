import pickle
from logging import getLogger

from desktop_utils.defaults import LOCALBOX_OPENFILES


def add(filename):
    openfiles_list = load()
    if not openfiles_list:
        openfiles_list = list()
    if not filename in openfiles_list:
        openfiles_list.append(filename)
    save(openfiles_list)


def save(openfiles_list):
    pickle.dump(openfiles_list, open(LOCALBOX_OPENFILES, 'wb'))


def load():
    try:
        with open(LOCALBOX_OPENFILES, 'rb') as f:
            openfiles_list = pickle.load(f)
            getLogger(__name__).debug('found this openned files: %s' % openfiles_list)
            return openfiles_list
    except IOError:
        openfiles_list = list()
        save(openfiles_list)
