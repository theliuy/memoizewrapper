import functools

from . import keygenerator
from . import storage


class _MemoizeStorageManager(object):
    """
        :type _key_generator: keygenerator.BaseKeyGenerator
        :type _storage: storage.BaseStorage
        :type _escape_cache_if:
    """

    def __init__(self,
                 func,
                 key_generator,
                 storage_ins,
                 escape_cache_if=None):
        """

        :param func: decorated function
        :type func: callable
        :param key_generator: instance of key generator
        :type key_generator: keygenerator.BaseKeyGenerator
        :param storage_ins: instance of storage
        :type storage_ins: storage.BaseStorage
        :param escape_cache_if: do not cache if the return value is True
        :type escape_cache_if:
        :return:

        """
        if not isinstance(key_generator, keygenerator.BaseKeyGenerator):
            raise TypeError('Key generator must be a sub-class of BaseKeyGenerator')
        if not isinstance(storage, storage.BaseStorage):
            raise TypeError('Storage must be a sub-class of BaseStorage')

        self._func = func

        self._storage = storage_ins
        self._key_generator = key_generator
        self._key_generator.register_function_parameters(func)

        # use a simple lambda function to avoid None check when use it
        self._escape_cache_if = escape_cache_if if escape_cache_if is not None else lambda x: False

    def __call__(self, *args, **kwargs):
        """

        :param func: decorated function
        :type func: callable
        :return:
        """

        key = self._key_generator.generate_key(*args, **kwargs)

        try:
            value = self._storage.get(key)
        except storage.CacheMissingError:
            # cache misses. call the function and reset it.
            value = self._func(*args, **kwargs)

            if not self._escape_cache_if(value):
                self._storage.set(key, value)

        return value

    # noinspection PyUnusedLocal
    def __get__(self, obj, obj_type):
        return functools.partial(self.__call__, obj)

    def flush(self):
        self._storage.flush()


def memorize_wrapper(*args, **kwargs):
    def wrapped_manager(func):
        manager = _MemoizeStorageManager(func, *args, **kwargs)
        return manager
    return wrapped_manager


def expiring_memoize(key_template, expiration, deepcopy=False, escape_cache_if=None):
    return memorize_wrapper(
        keygenerator.TupleKeyGenerator(template=key_template),
        storage.ExpiringStorage(expiration=expiration, deepcopy=deepcopy),
        escape_cache_if=escape_cache_if,
    )


def lru_memoize(key_template, capacity, deepcopy=False, escape_cache_if=None):
    return memorize_wrapper(
        keygenerator.TupleKeyGenerator(template=key_template),
        storage.LruStorage(capacity=capacity, deepcopy=deepcopy),
        escape_cache_if=escape_cache_if,
    )
