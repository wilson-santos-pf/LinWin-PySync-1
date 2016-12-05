import pickle
from logging import getLogger

from sync.defaults import LOCALBOX_SHARES_PATH
from sync.localbox import LocalBox
from sync.database import database_execute


class SharesController(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SharesController, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not hasattr(self, '_list'):
            self._logged_in = False
            self._list = list()

    def add(self, item):
        self._list.append(item)
        self.save()

    def delete(self, index, save=False):
        """
        Delete item from list by 'index'
        :param index:
        :param save:
        :return:
        """
        item = self._list[index]
        localbox_client = LocalBox(url=item.url, label=item.label)
        localbox_client.delete(item.path)
        sql = 'delete from keys where site = ? and user != ?'
        database_execute(sql, (item.label, item.user))
        del self._list[index]
        if save:
            self.save()

    def save(self):
        pickle.dump(self._list, open(LOCALBOX_SHARES_PATH, 'wb'))

    def load(self):
        try:
            self._list = pickle.load(open(LOCALBOX_SHARES_PATH, 'rb'))
        except IOError as error:
            getLogger(__name__).warn('%s' % error)

        return self._list


class ShareItem:
    def __init__(self, user=None, path=None, url=None, label=None):
        self.user = user
        self.path = path
        self.url = url
        self.label = label
