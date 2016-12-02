import pickle
from logging import getLogger

from sync.defaults import LOCALBOX_SHARES_PATH


class SharesController:
    def __init__(self):

        self._list = list()

    def add(self, item):
        self._list.append(item)
        self.save()

    def delete(self, index, save=False):
        """
        Delete item from list by 'index'
        :param index:
        :return:
        """
        label = self._list[index].label
        del self._list[index]
        if save:
            self.save()
        return label

    def save(self):
        pickle.dump(self._list, open(LOCALBOX_SHARES_PATH, 'wb'))

    def load(self):
        try:
            self._list = pickle.load(open(LOCALBOX_SHARES_PATH, 'rb'))
        except IOError as error:
            getLogger(__name__).warn('%s' % error)

        return self._list
