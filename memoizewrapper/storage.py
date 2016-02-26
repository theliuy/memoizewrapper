import collections
import copy
import threading
import time


class CacheMissingError(Exception):
    """ Error raised when cache was missing

    """
    pass


class BaseStorage(object):
    """ Storage Interface.

    """

    def __init__(self, deepcopy=False):
        """ init

        :param deepcopy: if the data needs to be deepcopied once it is set/gotten
        :type deepcopy: bool
        :return:
        """
        self.deepcopy = deepcopy

    def get(self, key):
        """ Get data from storage

        :param key: data key
        :type key: basestring
        :return:
        """
        raise NotImplementedError()

    def set(self, key, value, *args, **kwargs):
        """ Set data into storage

        :param key: storage key
        :param value: data value
        :return:
        """
        raise NotImplementedError()

    def delete(self, key):
        """ Delete data from storage

        :param key: data key
        :return:
        """

    def flush(self):
        """ Flush the data in the storage

        :return:
        """
        raise NotImplementedError()


class TimeToLiveStorage(BaseStorage):
    """ Use a dict object as the storage and provides simple functionality.


    """

    _StoredData = collections.namedtuple('_StoredData', ('expiration', 'value'))

    def __init__(self, *args, **kwargs):
        super(TimeToLiveStorage, self).__init__(*args, **kwargs)

        self._cache = {}
        self._lock = threading.Lock()

    def get(self, key):
        """ Get data by key

        We are doing lazy evaluation in get(). If the data is out of date, the stored tuple will be removed.

        :param key: data key
        :return:
        :raises: CacheMissingError
        """
        with self._lock:
            if key not in self._cache:
                raise CacheMissingError()

            stored_data = self._cache[key]
            if stored_data.expiration is not None and stored_data.expiration < time.time():
                del self._cache[key]
                raise CacheMissingError()
            return stored_data.value if not self.deepcopy else copy.deepcopy(stored_data.value)

    def set(self, key, value, expiration=None, *args, **kwargs):
        """ Set a (key, value) pair into the storage.

        :param key:
        :param value:
        :param expiration: data expiration. None donates never expired
        :return:
        """

        with self._lock:
            if self.deepcopy:
                value = copy.deepcopy(value)
            expiration = time.time() + expiration if expiration else None
            self._cache[key] = self._StoredData(expiration, value)

    def delete(self, key):
        """ remove data by key

        :param key:
        :return:
        :raises: CacheMissingError
        """
        with self._lock:
            try:
                del self._cache[key]
            except KeyError:
                raise CacheMissingError()

    def flush(self):
        with self._lock:
            self._cache.clear()
