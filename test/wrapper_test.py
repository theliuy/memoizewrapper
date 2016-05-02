import time
import unittest

import memoizewrapper.wrapper


class WrapperUnittest(unittest.TestCase):

    def test_expiring_memoize(self):
        expiration = 5  # 5 seconds
        called = 0

        @memoizewrapper.wrapper.expiring_memoize(('a', 'b'), expiration)
        def sum_int(a, b):
            nonlocal called
            called += 1
            return a + b

        self.assertEqual(sum_int(1, 2), 3)
        self.assertEqual(called, 1)

        self.assertEqual(sum_int(1, 2), 3)
        self.assertEqual(called, 1)

        self.assertEqual(sum_int(3, 4), 7)
        self.assertEqual(called, 2)

        self.assertEqual(sum_int(3, 4), 7)
        self.assertEqual(called, 2)

        self.assertEqual(sum_int(1, 2), 3)
        self.assertEqual(called, 2)

        time.sleep(expiration)

        self.assertEqual(sum_int(1, 2), 3)
        self.assertEqual(called, 3)

        self.assertEqual(sum_int(3, 4), 7)
        self.assertEqual(called, 4)

        sum_int.flush()

        self.assertEqual(sum_int(1, 2), 3)
        self.assertEqual(called, 5)

        self.assertEqual(sum_int(3, 4), 7)
        self.assertEqual(called, 6)

    def test_expiring_memoize_template(self):
        expiration = 5
        called = 0

        @memoizewrapper.wrapper.expiring_memoize(('a',), expiration)
        def only_care_a(a, b):
            nonlocal called
            called += 1
            return a + b

        self.assertEqual(only_care_a(1, 2), 3)
        self.assertEqual(called, 1)
        self.assertEqual(only_care_a(1, 5), 3)
        self.assertEqual(called, 1)

    def test_expiring_memoize_escape_cache(self):
        expiration = 5  # 5 sec
        called = 0

        def eq_1(val):
            return val == 1

        @memoizewrapper.wrapper.expiring_memoize(('a', 'b'), expiration, escape_cache_if=eq_1)
        def simple_return(a, b):
            nonlocal called
            called += 1
            return a + b

        # since it returns 1, it is not expected to be cache
        self.assertEqual(simple_return(0, 1), 1)
        self.assertEqual(called, 1)
        self.assertEqual(simple_return(0, 1), 1)
        self.assertEqual(called, 2)

        # since it returns 3, it is expected to be cache
        self.assertEqual(simple_return(2, 1), 3)
        self.assertEqual(called, 3)
        self.assertEqual(simple_return(2, 1), 3)
        self.assertEqual(called, 3)

    def test_lru_storage_get_set_delete(self):
        test_data = (
            'hello',
            'hi',
            'hey',
            'greeting',
            'Ciao',
        )
        capacity = 3
        called = 0
        expected_called = 0

        @memoizewrapper.wrapper.lru_memoize(('value',), capacity)
        def return_same(value):
            nonlocal called
            called += 1
            return value

        for i, val in enumerate(test_data):
            expected_called += 1
            self.assertEqual(return_same(val), val)
            self.assertEqual(called, expected_called)

        # test_data[2 ... 4] are currently in the storage
        # touch test_data[2] and insert a new key/value pair, check if test_data[3] was popped
        self.assertEqual(return_same(test_data[2]), test_data[2])
        self.assertEqual(called, expected_called)
        self.assertEqual(return_same(test_data[0]), test_data[0])
        expected_called += 1
        self.assertEqual(called, expected_called)
        self.assertEqual(return_same(test_data[3]), test_data[3])
        expected_called += 1
        self.assertEqual(called, expected_called)


if __name__ == '__main__':
    unittest.main()
