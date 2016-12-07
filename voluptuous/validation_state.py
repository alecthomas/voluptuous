import collections
import copy
from functools import wraps


def check_cache(validator_func):
    @wraps(validator_func)
    def state_wrapper(state, data):
        if isinstance(state, list):
            path = state
            state = ValidationState()
            state += path
        return state.check_cache(validator_func, data)
    return state_wrapper


class StateValidator(object):
    """Interface that is used to determine a special kind of callable object

    Subclasses of this class must implement __call__ consistent with the original
    signature. The provided signature allows one to pass the state to sub-validators.
    """

    def __call__(self, data, state=None):
        raise NotImplementedError


class ValidationState(object):
    """State of the validation, includes the path and cache.

    This class acts a lot like a list.

    The ValidationState _path is generally constant for the life of an instance.
    Instead of adding to the _path, a new instance is created with a unique path,
    but a shared cache.
    """

    def __init__(self, state=None):
        if state is None:
            self._path = []
            self._cache = collections.defaultdict(dict)

        elif isinstance(state, ValidationState):
            # prevent modification of higher path
            self._path = list(state._path)
            # build on "parent" cache
            self._cache = state._cache

        else:
            raise TypeError('Cannot initialize ValidationState with {}'.format(state))

    def __repr__(self):
        return '<ValidationState{}>'.format(self)

    def __str__(self):
        if self._path:
            return ' @ data[%s]' % ']['.join(map(repr, self._path))
        else:
            return ''

    def check_cache(self, validator_func, data):
        data_id = id(data)
        func_cache = self._cache[validator_func]
        if data_id not in func_cache:
            func_cache[data_id] = validator_func(self, data)
        return func_cache[data_id]

    def __add__(self, other):
        result = ValidationState(self)
        if isinstance(other, list):
            result._path += other
        elif isinstance(other, ValidationState):
            result._path += other._path
        else:
            raise ValueError("Cannot add other (type={}) to ValidationState"
                             .format(type(other)))
        return result

    def __iter__(self):
        return iter(self._path)

    def __len__(self):
        return len(self._path)
