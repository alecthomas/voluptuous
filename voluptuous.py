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

import re
import urlparse


class Error(Exception):
    """Base validation exception."""


class SchemaError(Error):
    """An error was encountered in the schema."""


class Invalid(Error):
    """
    """
    def __init__(self, message, path=None):
        Exception.__init__(self, message)
        self.path = path or []

    def __str__(self):
        return Exception.__str__(self) + (' near %r' % '/'.join(self.path)
                                          if self.path else '')


class Schema(object):
    """A validation schema.

    The schema is a Python tree-like structure where nodes are pattern
    matched against corresponding trees of values.

    Nodes can be values, in which case a direct comparison is used, types,
    in which case an isinstance() check is performed, or callables, which will
    validate and optionally convert the value.

    >>> validate = Schema({'one': {'two': 'three', 'four': 'five'}})
    >>> try:
    ...   validate({'one': {'four': 'six'}})
    ... except Invalid, e:
    ...   print e
    ...   print e.path
    not a valid value near 'one/four'
    ['one', 'four']
    """

    def __init__(self, schema):
        self.schema = schema

    def __call__(self, data):
        return self.validate([], self.schema, data)

    def validate(self, path, schema, data):
        if type(schema) is type:
            type_ = schema
        else:
            type_ = type(schema)

        try:
            if type_ is dict:
                return self.validate_dict([], schema, data)
            elif type_ is list:
                return self.validate_list([], schema, data)
            elif type_ in (int, long, str, unicode, float, complex, object) \
                    or callable(schema):
                return self.validate_scalar(schema, data)
            raise SchemaError('unknown data type %r' % type_)
        except AssertionError, e:
            raise Invalid(str(e), path)
        except Invalid, e:
            raise Invalid(e.args[0], path + e.path)

    def validate_dict(self, path, schema, data):
        """Validate a dictionary.

        A dictionary schema can contain a set of values, or at most one
        validator function/type.

        A dictionary schema will only validate a dictionary:

            >>> validate = Schema({})
            >>> validate([])
            Traceback (most recent call last):
            ...
            Invalid: expected a dictionary

        An invalid dictionary value:

            >>> validate = Schema({'one': 'two', 'three': 'four'})
            >>> validate({'one': 'three'})
            Traceback (most recent call last):
            ...
            Invalid: not a valid value near 'one'

        An invalid key:

            >>> validate({'two': 'three'})
            Traceback (most recent call last):
            ...
            Invalid: not a valid key

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
            Invalid: expected int value near '10'

        Wrap them in the coerce() function to achieve this:

            >>> validate = Schema({'one': 'two', 'three': 'four',
            ...                    coerce(int): str})
            >>> validate({'10': 'twenty'})
            {10: 'twenty'}

        (This is to avoid unexpected surprises.)
        """
        assert isinstance(data, dict), 'expected a dictionary'

        # If the schema dictionary is empty we accept any data dictionary.
        if not schema:
            return data

        key_schema = value_schema = None
        for key in schema:
            if type(key) is type or callable(key):
                if key_schema is not None:
                    raise SchemaError('only one key in a schema dictionary '
                                      'may be a validator')
                key_schema = key
                value_schema = schema[key]

        out = {}
        for key, value in data.iteritems():
            key_path = path + [key]
            if key in schema:
                value = self.validate(key_path, schema[key], value)
            else:
                if key_schema is None:
                    raise Invalid('not a valid key')
                key = self.validate(key_path, key_schema, key)
                value = self.validate(key_path, value_schema, value)
            out[key] = value
        return out

    def validate_list(self, path, schema, data):
        """Validate a list.

        A list is, despite the name, a *set* of valid values, and at most one
        optional validator.  Ordering is not enforced by the schema.

        >>> validator = Schema(['one', 'two', int])
        >>> validator(['one'])
        ['one']
        >>> validator([3.5])
        Traceback (most recent call last):
        ...
        Invalid: expected int value
        >>> validator([1])
        [1]
        """
        assert isinstance(data, list), 'expected a list'

        # Empty list schema, allow any data list.
        if not schema:
            return data

        value_schema = None
        for value in schema:
            if type(value) is type or callable(value):
                if value_schema is not None:
                    raise SchemaError('only one value in a schema list may be '
                                      'a validator')
                value_schema = value

        schema = set(schema)

        out = []
        for i, value in enumerate(data):
            if value not in schema:
                value = self.validate(path, value_schema, value)
            out.append(value)
        return out

    @staticmethod
    def validate_scalar(schema, data):
        """A scalar value.

        The schema can either be a value or a type.
        """
        if type(schema) is type:
            assert isinstance(data, schema), \
                    'expected %s value' % schema.__name__
        elif callable(schema):
            return schema(data)
        else:
            assert data == schema, 'not a valid value'
        return data


def coerce(type, msg=None):
    """Coerce a value to a type.

    If the type constructor throws a ValueError, the value will be marked as
    Invalid.
    """
    def f(v):
        try:
            return type(v)
        except ValueError:
            raise Invalid(msg or ('expected %s type' % type.__name__))
    return f


def true(msg=None):
    """Assert that a value is true, in the Python sense.

    >>> validate = Schema(true())

    "In the Python sense" means that implicitly false values, such as empty
    lists, dictionaries, etc. are treated as "false":

    >>> validate([])
    Traceback (most recent call last):
    ...
    Invalid: value was not true
    >>> validate([1])
    [1]
    >>> validate(False)
    Traceback (most recent call last):
    ...
    Invalid: value was not true

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

    >>> validate = Schema(any('true', 'false', coerce(bool)))
    >>> validate('true')
    'true'
    >>> validate(1)
    True
    """
    msg = kwargs.pop('msg', None)

    def f(v):
        for validator in validators:
            try:
                return Schema.validate_scalar(validator, v)
            except (Invalid, AssertionError):
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

    def f(v):
        try:
            for validator in validators:
                v = Schema.validate_scalar(validator, v)
        except (AssertionError, Invalid), e:
            raise Invalid(msg or str(e))
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
    Invalid: does not match regular expression

    Pattern may also be a compiled regular expression:

    >>> validate = Schema(match(re.compile(r'0x[A-F0-9]+', re.I)))
    >>> validate('0x123ef4')
    '0x123ef4'
    """
    if isinstance(pattern, basestring):
        pattern = re.compile(pattern)

    def f(v):
        assert pattern.match(v), (msg or 'does not match regular expression')
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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
