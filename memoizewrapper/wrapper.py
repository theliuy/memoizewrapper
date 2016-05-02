import functools

from . import keygenerator
from . import storage


class _MemoizeStorageManager(object):
    """
        :type _key_generator_register_kwargs: dict
        :type _key_generator: keygenerator.BaseKeyGenerator
        :type _storage: storage.BaseStorage
        :type _escape_cache_if:
    """

    def __init__(self,
                 func,
                 key_generator_cls=keygenerator.TupleKeyGenerator,
                 key_generator_register_kwargs=None,
                 storage_cls=storage.ExpiringStorage,
                 storage_init_kwargs=None,
                 escape_cache_if=None):
        """

        :param func: decorated function
        :type func: callable
        :param key_generator_cls: the class of create key generator instance
        :type key_generator_cls: type(keygenerator.BaseKeyGenerator)
        :param key_generator_register_kwargs: named parameters when register the wrapped function with key generator
        :param storage_cls: the class of storage
        :type storage_cls: type(storage.BaseStorage)
        :param storage_init_kwargs: named parameters to create storage instance
        :type storage_init_kwargs: dict
        :param escape_cache_if: do not cache if the return value is True
        :type escape_cache_if:
        :return:

        """
        if not issubclass(key_generator_cls, keygenerator.BaseKeyGenerator):
            raise TypeError('Key generator class must be a sub-class of BaseKeyGenerator')
        if not issubclass(storage_cls, storage.BaseStorage):
            raise TypeError('Storage class must be a sub-class of BaseStorage')

        self._func = func

        self._key_generator_register_kwargs = key_generator_register_kwargs or {}
        storage_init_kwargs = storage_init_kwargs or {}

        self._storage = storage_cls(**storage_init_kwargs)
        self._key_generator = key_generator_cls()
        self._key_generator.register_function_parameters(self._func, **self._key_generator_register_kwargs)

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
        key_generator_cls=keygenerator.TupleKeyGenerator,
        key_generator_register_kwargs={'template': key_template},
        storage_cls=storage.ExpiringStorage,
        storage_init_kwargs={'expiration': expiration, 'deepcopy': deepcopy},
        escape_cache_if=escape_cache_if,
    )


def lru_memoize(key_template, capacity, deepcopy=False, escape_cache_if=None):
    return memorize_wrapper(
        key_generator_cls=keygenerator.TupleKeyGenerator,
        key_generator_register_kwargs={'template': key_template},
        storage_cls=storage.LruStorage,
        storage_init_kwargs={'capacity': capacity, 'deepcopy': deepcopy},
        escape_cache_if=escape_cache_if,
    )
