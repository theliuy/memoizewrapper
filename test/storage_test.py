import unittest
import memoizewrapper.storage

__author__ = 'theliuy (liuyruc@gmail.com)'


class StorageTest(unittest.TestCase):

    def test_timetolive_storage_get_set_delete(self):
        store = memoizewrapper.storage.TimeToLiveStorage()

        test_key = 'hello'
        test_key_missing = 'nobody'
        test_value = 'world'
        store.set(test_key, test_value)

        self.assertEqual(store.get(test_key), test_value)

        self.assertRaises(memoizewrapper.storage.CacheMissingError, store.get, test_key_missing)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, store.delete, test_key_missing)

        store.delete(test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, store.get, test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, store.delete, test_key)

    def test_timetolive_simple_storage_flush(self):
        store = memoizewrapper.storage.TimeToLiveStorage()

        test_key = 'hello'
        test_key_missing = 'nobody'
        test_value = 'world'

        store.set(test_key, test_value)
        self.assertEqual(store.get(test_key), test_value)

        store.flush()
        self.assertRaises(memoizewrapper.storage.CacheMissingError, store.get, test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, store.delete, test_key)


if __name__ == '__main__':
    unittest.main()
