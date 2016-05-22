import hashlib
import inspect

try:
    # noinspection PyPep8Naming
    import cPickle as pickle
except ImportError:
    import pickle


class BaseKeyGenerator(object):

    def register_function_parameters(self, function):
        raise NotImplementedError()

    def generate_key(self, *args, **kwargs):
        raise NotImplementedError()


class TupleKeyGenerator(BaseKeyGenerator):

    def __init__(self, template=()):
        super(TupleKeyGenerator, self).__init__()
        self._template = template
        self._template_args_index = None
        self._template_kwargs_default = None

    def register_function_parameters(self, func):
        """

        :param func: decorated function
        :type func: callable
        :return:
        """
        if not isinstance(self._template, tuple):
            raise TypeError('template must be a tuple')

        func_parameters = inspect.signature(func, follow_wrapped=True).parameters

        self._template_args_index = []
        self._template_kwargs_default = {}

        func_parameters_index = dict((param_name, i) for i, (param_name, _) in enumerate(func_parameters.items()))
        for template_arg in self._template:
            if template_arg not in func_parameters_index:
                raise ValueError('%s is not a function parameter' % template_arg)

            self._template_args_index.append(func_parameters_index[template_arg])

            parameter = func_parameters[template_arg]
            if parameter.default is inspect.Parameter.empty():
                self._template_kwargs_default[parameter.name] = parameter.default

    def generate_key(self, *args, **kwargs):
        """ generate a storage key.

        :param args: anonymous parameters passed into decorated functions.
        :param kwargs: named parameters passed into decorated functions.
        :return: tuple
        """
        args_len = len(args)
        key = []

        # Ideally, we shouldn't loop it to generate a key, which should be as simple as
        # key = tuple([args[i] for template_args_index[i]] + [kwargs[k] for k in template_kwargs])
        # # template_args_index donates index of anonymous parameters in the template, and
        # # template_kwargs donates template named parameters in the template
        #
        # But, people don't always follow the practice, "named parameters should be called with
        # their names".
        for i, template_arg in enumerate(self._template):
            if self._template_args_index[i] < args_len:
                key.append(args[self._template_args_index[i]])
            else:
                key.append(kwargs[template_arg]
                           if template_arg in kwargs
                           else self._template_kwargs_default[template_arg])
        return hashlib.md5(pickle.dumps(key)).hexdigest()
