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

        :param deepcopy: if the data needs to be deep-copied once it is set/gotten
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

    def set(self, key, value):
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


class ExpiringStorage(BaseStorage):
    """ Use a dict object as the storage and provides simple functionality.
        The stored data has an expiration

        Further thought:
            An active thread can be used to clean the expired data.
    """

    _StoredData = collections.namedtuple('_StoredData', ('expiration', 'value'))

    def __init__(self, *args, **kwargs):
        self._expiration = kwargs.pop('expiration', None)
        super(ExpiringStorage, self).__init__(*args, **kwargs)

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

    def set(self, key, value):
        """ Set a (key, value) pair into the storage.

        :param key:
        :param value:
        :return:
        """

        if self.deepcopy:
            value = copy.deepcopy(value)
        expiration = time.time() + self._expiration if self._expiration is not None else None
        with self._lock:
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


class LruStorage(BaseStorage):
    """ LruStorage provides a storage with latest recent use algorithm.
        "Use" is determined by both get() and set().

        It is implemented as a hash table and a double-linked list. Hash table gives a O(1)
        like query. And double-linked list presents when data was touched.
    """

    class _DataNode(object):
        """ A nested data class
        """

        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.left, self.right = None, None

    def __init__(self, *args, **kwargs):
        self._capacity = kwargs.pop('capacity', None)
        if not self._capacity:
            raise ValueError('Capacity must be a positive integer/long.')

        super(LruStorage, self).__init__(*args, **kwargs)
        self._lock = threading.Lock()

        # the hash table maintain the mapping between key and values
        self._data = {}

        # double-linked list head
        self._head = None

        # since I don't believe the performance of len(dict), let do this
        self._size = 0

    def __del__(self):
        self.flush()

    def get(self, key):
        with self._lock:
            node = self._data.get(key)

            if node is None:
                raise CacheMissingError()

            self._dli_touch(node)
            return node.value if not self.deepcopy else copy.deepcopy(node.value)

    def set(self, key, value):
        if self.deepcopy:
            value = copy.deepcopy(value)

        with self._lock:
            node = self._data.get(key)

            if node is None:
                # it is a new key to set
                if self._capacity <= self._size:
                    # we hit the floor, remove one node from the storage
                    node_to_remove = self._head.left
                    self._dli_remove_node(node_to_remove)
                    del self._data[node_to_remove.key]
                    self._size -= 1

                node = self._DataNode(key, value)
                self._dli_push_front(node)
                self._data[key] = node

                self._size += 1
            else:
                # we already have the key, just update the value and touch it.
                # Even if the value is the same as what it was, touch it
                node.value = value
                self._dli_touch(node)

    def delete(self, key):
        with self._lock:
            node = self._data.get(key)

            if node is None:
                raise CacheMissingError()

            self._dli_remove_node(node)
            del self._data[key]
            self._size -= 1

    def flush(self):
        """ flush() on a Lru storage is a quite expensive, to avoid cycled memory garbage.

        :return:
        """
        with self._lock:
            for data_node in self._data.values():
                data_node.left = None
                data_node.right = None
            self._data.clear()
            self._head = None
            self._size = 0

    @property
    def size(self):
        return self._size

    def _dli_remove_node(self, node):
        """ Remove a node from linked list

        :param node:
        :return:
        """
        if node == self._head:
            self._head = node.right if node.right != node else None

        node.left.right, node.right.left = node.right, node.left
        node.left, node.right = None, None

    def _dli_push_front(self, node):
        if self._head:
            node.left = self._head.left
            node.right = self._head
            self._head.left.right = node
            self._head.left = node
        else:
            node.left, node.right = node, node
        self._head = node

    def _dli_touch(self, node):
        """ Touch the double-linked list.
            Let the node the be the most recent modified data node.

            :type node: _DataNode
        """
        if self._size <= 1 or node == self._head:
            return

        self._dli_remove_node(node)
        self._dli_push_front(node)
