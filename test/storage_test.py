import time
import unittest

import memoizewrapper.storage

__author__ = 'theliuy (liuyruc@gmail.com)'


class StorageTest(unittest.TestCase):

    def test_expiring_storage_get_set_delete(self):
        storage = memoizewrapper.storage.ExpiringStorage()

        test_key = 'hello'
        test_key_missing = 'nobody'
        test_value = 'world'
        test_value_updated = 'new world'
        storage.set(test_key, test_value)

        self.assertEqual(storage.get(test_key), test_value)

        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, test_key_missing)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.delete, test_key_missing)

        storage.set(test_key, test_value_updated)
        self.assertEqual(storage.get(test_key), test_value_updated)

        storage.delete(test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.delete, test_key)

    def test_expiring_storage_flush(self):
        storage = memoizewrapper.storage.ExpiringStorage()

        test_key = 'hello'
        test_value = 'world'

        storage.set(test_key, test_value)
        self.assertEqual(storage.get(test_key), test_value)

        storage.flush()
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.delete, test_key)

    def test_expiring_storage_timeout(self):
        test_key = 'hello'
        test_value = 'world'
        time_to_live = 5  # 5 second

        storage = memoizewrapper.storage.ExpiringStorage(expiration=time_to_live)

        storage.set(test_key, test_value)
        self.assertEquals(storage.get(test_key), test_value)
        time.sleep(time_to_live)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, test_key)

    def test_lru_storage_get_set_delete(self):
        test_data = (
            ('hello', 'world'),
            ('hi', 'yang'),
            ('hey', 'Beijing'),
            ('greeting', 'traveler'),
            ('Ciao', 'Mondo'),
        )
        test_storage_size = 3
        storage = memoizewrapper.storage.LruStorage(capacity=test_storage_size)

        for i, (key, value) in enumerate(test_data):
            # check if the size is right at the beginning
            self.assertEqual(storage.size, min(i, test_storage_size))

            # check basic set/get
            storage.set(key, value)
            self.assertEqual(storage.get(key), value)

            # check if oversize values were popped
            if i >= test_storage_size:
                for j in range(i - test_storage_size + 1):
                    missing_key = test_data[j][0]
                    self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, missing_key)
                    self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.delete, missing_key)

            self.assertEqual(storage.size, min(i + 1, test_storage_size))

        # test_data[2 ... 4] are currently in the storage
        # touch test_data[2] and insert a new key/value pair, check if test_data[3] was popped
        storage.get(test_data[2][0])
        storage.set(*test_data[0])
        self.assertEqual(storage.get(test_data[2][0]), test_data[2][1])
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, test_data[3][0])

        # test update with full storage
        test_key = test_data[2][0]
        test_value_updated = 'foo'
        storage.set(test_key, test_value_updated)
        self.assertEqual(storage.get(test_key), test_value_updated)

        # test delete
        test_key = test_data[4][0]
        storage.delete(test_key)
        self.assertRaises(memoizewrapper.storage.CacheMissingError, storage.get, test_key)

        # test update with non-full storage
        test_key = test_data[2][0]
        test_value_updated = 'bar'
        storage.set(test_key, test_value_updated)
        self.assertEqual(storage.get(test_key), test_value_updated)


if __name__ == '__main__':
    unittest.main()
