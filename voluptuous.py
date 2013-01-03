# encoding: utf-8
#
# Copyright (C) 2010 Alec Thomas <alec@swapoff.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Alec Thomas <alec@swapoff.org>

"""Schema validation for Python data structures.

Given eg. a nested data structure like this:

    {
        'exclude': ['Users', 'Uptime'],
        'include': [],
        'set': {
            'snmp_community': 'public',
            'snmp_timeout': 15,
            'snmp_version': '2c',
        },
        'targets': {
            'localhost': {
                'exclude': ['Uptime'],
                'features': {
                    'Uptime': {
                        'retries': 3,
                    },
                    'Users': {
                        'snmp_community': 'monkey',
                        'snmp_port': 15,
                    },
                },
                'include': ['Users'],
                'set': {
                    'snmp_community': 'monkeys',
                },
            },
        },
    }

A schema like this:

    >>> settings = {
    ...   'snmp_community': str,
    ...   'retries': int,
    ...   'snmp_version': all(coerce(str), any('3', '2c', '1')),
    ... }
    >>> features = ['Ping', 'Uptime', 'Http']
    >>> schema = Schema({
    ...    'exclude': features,
    ...    'include': features,
    ...    'set': settings,
    ...    'targets': {
    ...      'exclude': features,
    ...      'include': features,
    ...      'features': {
    ...        str: settings,
    ...      },
    ...    },
    ... })

Validate like so:

    >>> schema({
    ...   'set': {
    ...     'snmp_community': 'public',
    ...     'snmp_version': '2c',
    ...   },
    ...   'targets': {
    ...     'exclude': ['Ping'],
    ...     'features': {
    ...       'Uptime': {'retries': 3},
    ...       'Users': {'snmp_community': 'monkey'},
    ...     },
    ...   },
    ... })  # doctest: +NORMALIZE_WHITESPACE
    {'set': {'snmp_version': '2c', 'snmp_community': 'public'},
     'targets': {'exclude': ['Ping'],
                 'features': {'Uptime': {'retries': 3},
                              'Users': {'snmp_community': 'monkey'}}}}
"""

import os
import re
import types
import urlparse


__author__ = 'Alec Thomas <alec@swapoff.org>'
__version__ = '0.5'


class Undefined(object):
    def __nonzero__(self):
        return False

    def __repr__(self):
        return '...'


UNDEFINED = Undefined()


class Error(Exception):
    """Base validation exception."""


class SchemaError(Error):
    """An error was encountered in the schema."""


class Invalid(Error):
    """The data was invalid.

    :attr msg: The error message.
    :attr path: The path to the error, as a list of keys in the source data.
    """

    def __init__(self, message, path=None):
        Exception.__init__(self, message)
        self.path = path or []

    @property
    def msg(self):
        return self.args[0]

    def __str__(self):
        path = ' @ data[%s]' % ']['.join(map(repr, self.path)) \
                if self.path else ''
        return Exception.__str__(self) + path


class InvalidList(Invalid):
    def __init__(self, errors=None):
        self.errors = errors[:] if errors else []

    @property
    def msg(self):
        return self.errors[0].msg

    @property
    def path(self):
        return self.errors[0].path

    def add(self, error):
        self.errors.append(error)

    def __str__(self):
        return str(self.errors[0])


class Schema(object):
    """A validation schema.

    The schema is a Python tree-like structure where nodes are pattern
    matched against corresponding trees of values.

    Nodes can be values, in which case a direct comparison is used, types,
    in which case an isinstance() check is performed, or callables, which will
    validate and optionally convert the value.
    """

    def __init__(self, schema, required=False, extra=False):
        """Create a new Schema.

        :param schema: Validation schema. See :module:`voluptuous` for details.
        :param required: Keys defined in the schema must be in the data.
        :param extra: Keys in the data need not have keys in the schema.
        """
        self.schema = schema
        self.required = required
        self.extra = extra

    def __call__(self, data):
        """Validate data against this schema."""
        return self.validate([], self.schema, data)

    def validate(self, path, schema, data):
        try:
            if isinstance(schema, dict):
                return self.validate_dict(path, schema, data)
            elif isinstance(schema, list):
                return self.validate_list(path, schema, data)
            elif isinstance(schema, tuple):
                return self.validate_tuple(path, schema, data)
            type_ = type(schema)
            if type_ is type:
                type_ = schema
            if type_ in (int, long, str, unicode, float, complex, object,
                         list, dict, types.NoneType) or callable(schema):
                return self.validate_scalar(path, schema, data)
        except InvalidList:
            raise
        except Invalid, e:
            raise InvalidList([e])
        raise SchemaError('unsupported schema data type %r' %
                          type(schema).__name__)

    def validate_dict(self, path, schema, data):
        """Validate a dictionary.

        A dictionary schema can contain a set of values, or at most one
        validator function/type.

        A dictionary schema will only validate a dictionary:

            >>> validate = Schema({})
            >>> validate([])
            Traceback (most recent call last):
            ...
            InvalidList: expected a dictionary

        An invalid dictionary value:

            >>> validate = Schema({'one': 'two', 'three': 'four'})
            >>> validate({'one': 'three'})
            Traceback (most recent call last):
            ...
            InvalidList: not a valid value for dictionary value @ data['one']

        An invalid key:

            >>> validate({'two': 'three'})
            Traceback (most recent call last):
            ...
            InvalidList: extra keys not allowed @ data['two']

        Validation function, in this case the "int" type:

            >>> validate = Schema({'one': 'two', 'three': 'four', int: str})

        Valid integer input:

            >>> validate({10: 'twenty'})
            {10: 'twenty'}

        By default, a "type" in the schema (in this case "int") will be used
        purely to validate that the corresponding value is of that type. It
        will not coerce the value:

            >>> validate({'10': 'twenty'})
            Traceback (most recent call last):
            ...
            InvalidList: extra keys not allowed @ data['10']

        Wrap them in the coerce() function to achieve this:

            >>> validate = Schema({'one': 'two', 'three': 'four',
            ...                    coerce(int): str})
            >>> validate({'10': 'twenty'})
            {10: 'twenty'}

        (This is to avoid unexpected surprises.)
        """
        if not isinstance(data, dict):
            raise Invalid('expected a dictionary', path)

        out = type(data)()
        required_keys = set(key for key in schema
                            if
                            (self.required and not isinstance(key, optional))
                            or
                            isinstance(key, required))
        error = None
        errors = []
        for key, value in data.iteritems():
            key_path = path + [key]
            for skey, svalue in schema.iteritems():
                if skey is extra:
                    new_key = key
                else:
                    try:
                        new_key = self.validate(key_path, skey, key)
                    except Invalid, e:
                        if len(e.path) > len(key_path):
                            raise
                        if not error or len(e.path) > len(error.path):
                            error = e
                        continue
                # Backtracking is not performed once a key is selected, so if
                # the value is invalid we immediately throw an exception.
                try:
                    out[new_key] = self.validate(key_path, svalue, value)
                except Invalid, e:
                    if len(e.path) > len(key_path):
                        errors.append(e)
                    else:
                        errors.append(Invalid(e.msg + ' for dictionary value',
                                e.path))
                    break

                # Key and value okay, mark any required() fields as found.
                required_keys.discard(skey)
                break
            else:
                if self.extra:
                    out[key] = value
                else:
                    errors.append(Invalid('extra keys not allowed',
                            key_path))
        for key in required_keys:
            errors.append(Invalid('required key not provided', path + [key]))
        if errors:
            raise InvalidList(errors)
        return out

    def _validate_sequence(self, path, schema, data, seq_type):
        """Validate a sequence type.

        This is a sequence of valid values or validators tried in order.

        >>> validator = Schema(['one', 'two', int])
        >>> validator(['one'])
        ['one']
        >>> validator([3.5])
        Traceback (most recent call last):
        ...
        InvalidList: invalid list value @ data[0]
        >>> validator([1])
        [1]
        """
        seq_type_name = seq_type.__name__
        if not isinstance(data, seq_type):
            raise Invalid('expected a %s' % seq_type_name, path)

        # Empty seq schema, allow any data.
        if not schema:
            return data

        out = []
        invalid = None
        errors = []
        index_path = UNDEFINED
        for i, value in enumerate(data):
            index_path = path + [i]
            invalid = None
            for s in schema:
                try:
                    out.append(self.validate(index_path, s, value))
                    break
                except Invalid, e:
                    if len(e.path) > len(index_path):
                        raise
                    invalid = e
            else:
                if len(invalid.path) <= len(index_path):
                    invalid = Invalid('invalid %s value' % seq_type_name, index_path)
                errors.append(invalid)
        if errors:
            raise InvalidList(errors)
        return type(data)(out)

    def validate_tuple(self, path, schema, data):
        """Validate a tuple.

        A tuple is a sequence of valid values or validators tried in order.

        >>> validator = Schema(('one', 'two', int))
        >>> validator(('one',))
        ('one',)
        >>> validator((3.5,))
        Traceback (most recent call last):
        ...
        InvalidList: invalid tuple value @ data[0]
        >>> validator((1,))
        (1,)
        """
        return self._validate_sequence(path, schema, data, seq_type=tuple)

    def validate_list(self, path, schema, data):
        """Validate a list.

        A list is a sequence of valid values or validators tried in order.

        >>> validator = Schema(['one', 'two', int])
        >>> validator(['one'])
        ['one']
        >>> validator([3.5])
        Traceback (most recent call last):
        ...
        InvalidList: invalid list value @ data[0]
        >>> validator([1])
        [1]
        """
        return self._validate_sequence(path, schema, data, seq_type=list)

    @staticmethod
    def validate_scalar(path, schema, data):
        """A scalar value.

        The schema can either be a value or a type.

        >>> Schema.validate_scalar([], int, 1)
        1
        >>> Schema.validate_scalar([], float, '1')
        Traceback (most recent call last):
        ...
        Invalid: expected float

        Callables have
        >>> Schema.validate_scalar([], lambda v: float(v), '1')
        1.0

        As a convenience, ValueError's are trapped:

        >>> Schema.validate_scalar([], lambda v: float(v), 'a')
        Traceback (most recent call last):
        ...
        Invalid: not a valid value
        """
        if isinstance(schema, type):
            if not isinstance(data, schema):
                raise Invalid('expected %s' % schema.__name__, path)
        elif callable(schema):
            try:
                return schema(data)
            except ValueError, e:
                raise Invalid('not a valid value', path)
            except Invalid, e:
                raise Invalid(e.msg, path + e.path)
        else:
            if data != schema:
                raise Invalid('not a valid value', path)
        return data


class marker(object):
    """Mark nodes for special treatment."""

    def __init__(self, schema, msg=None):
        self.schema = schema
        self._schema = Schema(schema)
        self.msg = msg

    def __call__(self, v):
        try:
            return self._schema(v)
        except Invalid, e:
            if not self.msg or len(e.path) > 1:
                raise
            raise Invalid(self.msg)

    def __str__(self):
        return str(self.schema)

    def __repr__(self):
        return repr(self.schema)


class optional(marker):
    """Mark a node in the schema as optional."""


class required(marker):
    """Mark a node in the schema as being required."""


def extra(_):
    """Allow keys in the data that are not present in the schema."""
    raise SchemaError('"extra" should never be called')


def msg(schema, msg):
    """Report a user-friendly message if a schema fails to validate.

    >>> validate = Schema(
    ...   msg(['one', 'two', int],
    ...       'should be one of "one", "two" or an integer'))
    >>> validate(['three'])
    Traceback (most recent call last):
    ...
    InvalidList: should be one of "one", "two" or an integer

    Messages are only applied to invalid direct descendants of the schema:

    >>> validate = Schema(msg([['one', 'two', int]], 'not okay!'))
    >>> validate([['three']])
    Traceback (most recent call last):
    ...
    InvalidList: invalid list value @ data[0][0]
    """
    schema = Schema(schema)
    def f(v):
        try:
            return schema(v)
        except Invalid, e:
            if len(e.path) > 1:
                raise e
            else:
                raise Invalid(msg)
    return f


def coerce(type, msg=None):
    """Coerce a value to a type.

    If the type constructor throws a ValueError, the value will be marked as
    Invalid.
    """
    def f(v):
        try:
            return type(v)
        except ValueError:
            raise Invalid(msg or ('expected %s' % type.__name__))
    return f


def true(msg=None):
    """Assert that a value is true, in the Python sense.

    >>> validate = Schema(true())

    "In the Python sense" means that implicitly false values, such as empty
    lists, dictionaries, etc. are treated as "false":

    >>> validate([])
    Traceback (most recent call last):
    ...
    InvalidList: value was not true
    >>> validate([1])
    [1]
    >>> validate(False)
    Traceback (most recent call last):
    ...
    InvalidList: value was not true

    ...and so on.
    """
    def f(v):
        if v:
            return v
        raise Invalid(msg or 'value was not true')
    return f


def false(msg=None):
    """Assert that a value is false, in the Python sense.

    (see :func:`true` for more detail)

    >>> validate = Schema(false())
    >>> validate([])
    []
    """
    def f(v):
        if not v:
            return v
        raise Invalid(msg or 'value was not false')
    return f


def boolean(msg=None):
    """Convert human-readable boolean values to a bool.

    Accepted values are 1, true, yes, on, enable, and their negatives.
    Non-string values are cast to bool.

    >>> validate = Schema(boolean())
    >>> validate(True)
    True
    >>> validate('moo')
    Traceback (most recent call last):
    ...
    InvalidList: expected boolean
    """
    def f(v):
        try:
            if isinstance(v, basestring):
                v = v.lower()
                if v in ('1', 'true', 'yes', 'on', 'enable'):
                    return True
                if v in ('0', 'false', 'no', 'off', 'disable'):
                    return False
                raise Invalid(msg or 'expected boolean')
            return bool(v)
        except ValueError:
            raise Invalid(msg or 'expected boolean')
    return f


def any(*validators, **kwargs):
    """Use the first validated value.

    :param msg: Message to deliver to user if validation fails.
    :returns: Return value of the first validator that passes.

    >>> validate = Schema(any('true', 'false',
    ...                       all(any(int, bool), coerce(bool))))
    >>> validate('true')
    'true'
    >>> validate(1)
    True
    >>> validate('moo')
    Traceback (most recent call last):
    ...
    InvalidList: no valid value found
    """
    msg = kwargs.pop('msg', None)
    schemas = [Schema(val) for val in validators]

    def f(v):
        for schema in schemas:
            try:
                return schema(v)
            except Invalid, e:
                if len(e.path) > 1:
                    raise
                pass
        else:
            raise Invalid(msg or 'no valid value found')
    return f


def all(*validators, **kwargs):
    """Value must pass all validators.

    The output of each validator is passed as input to the next.

    :param msg: Message to deliver to user if validation fails.

    >>> validate = Schema(all('10', coerce(int)))
    >>> validate('10')
    10
    """
    msg = kwargs.pop('msg', None)
    schemas = [Schema(val) for val in validators]

    def f(v):
        try:
            for schema in schemas:
                v = schema(v)
        except Invalid, e:
            raise Invalid(msg or e.msg)
        return v
    return f


def match(pattern, msg=None):
    """Value must match the regular expression.

    >>> validate = Schema(match(r'^0x[A-F0-9]+$'))
    >>> validate('0x123EF4')
    '0x123EF4'
    >>> validate('123EF4')
    Traceback (most recent call last):
    ...
    InvalidList: does not match regular expression

    Pattern may also be a compiled regular expression:

    >>> validate = Schema(match(re.compile(r'0x[A-F0-9]+', re.I)))
    >>> validate('0x123ef4')
    '0x123ef4'
    """
    if isinstance(pattern, basestring):
        pattern = re.compile(pattern)

    def f(v):
        if not pattern.match(v):
            raise Invalid(msg or 'does not match regular expression')
        return v
    return f


def sub(pattern, substitution, msg=None):
    """Regex substitution.

    >>> validate = Schema(all(sub('you', 'I'),
    ...                       sub('hello', 'goodbye')))
    >>> validate('you say hello')
    'I say goodbye'
    """
    if isinstance(pattern, basestring):
        pattern = re.compile(pattern)

    def f(v):
        return pattern.sub(substitution, v)
    return f


def url(msg=None):
    """Verify that the value is a URL."""
    def f(v):
        try:
            urlparse.urlparse(v)
            return v
        except:
            raise Invalid(msg or 'expected a URL')
    return f


def isfile(msg=None):
    """Verify the file exists."""
    def f(v):
        if os.path.isfile(v):
            return v
        else:
            raise Invalid(msg or 'not a file')
    return f


def isdir(msg=None):
    """Verify the directory exists."""
    def f(v):
        if os.path.isdir(v):
            return v
        else:
            raise Invalid(msg or 'not a directory')
    return f


def path_exists(msg=None):
    """Verify the path exists, regardless of its type."""
    def f(v):
        if os.path.exists(v):
            return v
        else:
            raise Invalid(msg or 'path does not exist')
    return f


def range(min=None, max=None, msg=None):
    """Limit a value to a range.

    Either min or max may be omitted.

    :raises Invalid: If the value is outside the range and clamp=False.
    """
    def f(v):
        if min is not None and v < min:
            raise Invalid(msg or 'value must be at least %s' % min)
        if max is not None and v > max:
            raise Invalid(msg or 'value must be at most %s' % max)
        return v
    return f


def clamp(min=None, max=None, msg=None):
    """Clamp a value to a range.

    Either min or max may be omitted.
    """
    def f(v):
        if min is not None and v < min:
            v = min
        if max is not None and v > max:
            v = max
        return v
    return f


def length(min=None, max=None, msg=None):
    """The length of a value must be in a certain range."""
    def f(v):
        if min is not None and len(v) < min:
            raise Invalid(msg or 'length of value must be at least %s' % min)
        if max is not None and len(v) > max:
            raise Invalid(msg or 'length of value must be at most %s' % max)
        return v
    return f


def lower(v):
    """Transform a string to lower case.

    >>> s = Schema(lower)
    >>> s('HI')
    'hi'
    """
    return str(v).lower()


def upper(v):
    """Transform a string to upper case.

    >>> s = Schema(upper)
    >>> s('hi')
    'HI'
    """
    return str(v).upper()


def capitalize(v):
    """Capitalise a string.

    >>> s = Schema(capitalize)
    >>> s('hello world')
    'Hello world'
    """
    return str(v).capitalize()


def title(v):
    """Title case a string.

    >>> s = Schema(title)
    >>> s('hello world')
    'Hello World'
    """
    return str(v).title()


def default_to(default_value, msg=None):
    """Sets a value to default_value if none provided.

    >>> s = Schema(default_to(42))
    >>> s(None)
    42
    """
    def f(v):
        if v is None:
            v = default_value
        return v
    return f


if __name__ == '__main__':
    import doctest
    doctest.testmod()
