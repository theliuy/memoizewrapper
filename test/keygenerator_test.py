try:
    # noinspection PyPep8Naming
    import cPickle as pickle
except ImportError:
    import pickle
import hashlib
import unittest

import memoizewrapper.keygenerator


class KeyGenerator(unittest.TestCase):

    def test_tuple_key_generator_with_function(self):
        generator = memoizewrapper.keygenerator.TupleKeyGenerator(template=('firstname', 'lastname', 'number'))

        def test_func(firstname, lastname, address=None, number=''):
            return firstname, lastname, address, number

        generator.register_function_parameters(test_func)

        test_firstname = 'hello'
        test_lastname = 'world'
        test_address = 'CA'
        test_number = '01010'
        test_expected_key_raw = [test_firstname, test_lastname, test_number]
        test_expected_result = hashlib.md5(pickle.dumps(test_expected_key_raw)).hexdigest()
        self.assertEquals(generator.generate_key(test_firstname,
                                                 test_lastname,
                                                 address=test_address,
                                                 number=test_number),
                          test_expected_result)
        self.assertEquals(generator.generate_key(test_firstname,
                                                 test_lastname,
                                                 number=test_number),
                          test_expected_result)
        self.assertEquals(generator.generate_key(test_firstname,
                                                 test_lastname,
                                                 number=test_number,
                                                 address=test_address),
                          test_expected_result)

        # Sometimes, people are bad.
        self.assertEquals(generator.generate_key(test_firstname,
                                                 test_lastname,
                                                 test_address,
                                                 test_number),
                          test_expected_result)
        self.assertEquals(generator.generate_key(test_firstname,
                                                 test_lastname,
                                                 test_address,
                                                 number=test_number),
                          test_expected_result)


if __name__ == '__main__':
    unittest.main()
