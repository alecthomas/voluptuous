==============================================
Voluptuous is a Python data validation library
==============================================

.. image:: https://travis-ci.org/alecthomas/voluptuous.png
    :alt: Build Status
    :target: https://travis-ci.org/alecthomas/voluptuous

.. image:: https://badge.waffle.io/alecthomas/voluptuous.png?label=ready&title=Ready
    :alt: Stories in Ready
    :target: https://waffle.io/alecthomas/voluptuous

Voluptuous, *despite* the name, is a Python data validation library. It is
primarily intended for validating data coming into Python as JSON, YAML, etc.

It has three goals:

1.  Simplicity.
2.  Support for complex data structures.
3.  Provide useful error messages.

Contact
=======

Voluptuous now has a mailing list! Send a mail to voluptuous@librelist.com
to subscribe. Instructions will follow.

You can also contact me directly via `email <alec@swapoff.org>`_ or
`Twitter <https://twitter.com/alecthomas>`_.

To file a bug, create a
`new issue <https://github.com/alecthomas/voluptuous/issues/new>`_
on GitHub with a short example of how to replicate the issue.

Show me an example
==================

Twitter's `user search API
<https://dev.twitter.com/docs/api/1/get/users/search>`_ accepts query URLs
like::

    $ curl 'http://api.twitter.com/1/users/search.json?q=python&per_page=20&page=1

To validate this we might use a schema like::

    >>> from voluptuous import Schema
    >>> schema = Schema({
    ...   'q': str,
    ...   'per_page': int,
    ...   'page': int,
    ... })

This schema very succinctly and roughly describes the data required by
the API, and will work fine. But it has a few problems. Firstly, it
doesn't fully express the constraints of the API. According to the API,
``per_page`` should be restricted to at most 20, defaulting to 5, for
example. To describe the semantics of the API more accurately, our
schema will need to be more thoroughly defined::

    >>> from voluptuous import Required, All, Length, Range
    >>> schema = Schema({
    ...   Required('q'): All(str, Length(min=1)),
    ...   Required('per_page', default=5): All(int, Range(min=1, max=20)),
    ...   'page': All(int, Range(min=0)),
    ... })

This schema fully enforces the interface defined in Twitter's
documentation, and goes a little further for completeness.

"q" is required::

    >>> from voluptuous import MultipleInvalid, Invalid
    >>> try:
    ...   schema({})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "required key not provided @ data['q']"
    True

...must be a string::

    >>> try:
    ...   schema({'q': 123})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "expected str for dictionary value @ data['q']"
    True

...and must be at least one character in length::

    >>> try:
    ...   schema({'q': ''})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "length of value must be at least 1 for dictionary value @ data['q']"
    True
    >>> schema({'q': '#topic'}) == {'q': '#topic', 'per_page': 5}
    True

``per_page`` is a positive integer no greater than 20::

    >>> try:
    ...   schema({'q': '#topic', 'per_page': 900})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "value must be at most 20 for dictionary value @ data['per_page']"
    True
    >>> try:
    ...   schema({'q': '#topic', 'per_page': -10})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "value must be at least 1 for dictionary value @ data['per_page']"
    True

``page`` is an integer ``>= 0``::

    >>> try:
    ...   schema({'q': '#topic', 'per_page': 'one'})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc)
    "expected int for dictionary value @ data['per_page']"
    >>> schema({'q': '#topic', 'page': 1}) == {'q': '#topic', 'page': 1, 'per_page': 5}
    True

Defining schemas
================

Schemas are nested data structures consisting of dictionaries, lists,
scalars and *validators*. Each node in the input schema is pattern
matched against corresponding nodes in the input data.

Literals
--------

Literals in the schema are matched using normal equality checks::

    >>> schema = Schema(1)
    >>> schema(1)
    1
    >>> schema = Schema('a string')
    >>> schema('a string')
    'a string'

Types
-----

Types in the schema are matched by checking if the corresponding value
is an instance of the type::

    >>> schema = Schema(int)
    >>> schema(1)
    1
    >>> try:
    ...   schema('one')
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "expected int"
    True

Lists
-----

Lists in the schema are treated as a set of valid values. Each element
in the schema list is compared to each value in the input data::

    >>> schema = Schema([1, 'a', 'string'])
    >>> schema([1])
    [1]
    >>> schema([1, 1, 1])
    [1, 1, 1]
    >>> schema(['a', 1, 'string', 1, 'string'])
    ['a', 1, 'string', 1, 'string']

Validation functions
--------------------

Validators are simple callables that raise an ``Invalid`` exception when
they encounter invalid data. The criteria for determining validity is
entirely up to the implementation; it may check that a value is a valid
username with ``pwd.getpwnam()``, it may check that a value is of a
specific type, and so on.

The simplest kind of validator is a Python function that raises
ValueError when its argument is invalid. Conveniently, many builtin
Python functions have this property. Here's an example of a date
validator::

    >>> from datetime import datetime
    >>> def Date(fmt='%Y-%m-%d'):
    ...   return lambda v: datetime.strptime(v, fmt)

::

    >>> schema = Schema(Date())
    >>> schema('2013-03-03')
    datetime.datetime(2013, 3, 3, 0, 0)
    >>> try:
    ...   schema('2013-03')
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "not a valid value"
    True

In addition to simply determining if a value is valid, validators may
mutate the value into a valid form. An example of this is the
``Coerce(type)`` function, which returns a function that coerces its
argument to the given type::

    def Coerce(type, msg=None):
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
    
This example also shows a common idiom where an optional human-readable
message can be provided. This can vastly improve the usefulness of the
resulting error messages.

Dictionaries
------------

Each key-value pair in a schema dictionary is validated against each
key-value pair in the corresponding data dictionary::

    >>> schema = Schema({1: 'one', 2: 'two'})
    >>> schema({1: 'one'})
    {1: 'one'}

Extra dictionary keys
`````````````````````

By default any additional keys in the data, not in the schema will
trigger exceptions::

    >>> schema = Schema({2: 3})
    >>> try:
    ...   schema({1: 2, 2: 3})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "extra keys not allowed @ data[1]"
    True

This behaviour can be altered on a per-schema basis with
``Schema(..., extra=True)``::

    >>> schema = Schema({2: 3}, extra=True)
    >>> schema({1: 2, 2: 3})
    {1: 2, 2: 3}

It can also be overridden per-dictionary by using the catch-all marker
token ``extra`` as a key:

    >>> from voluptuous import Extra
    >>> schema = Schema({1: {Extra: object}})
    >>> schema({1: {'foo': 'bar'}})
    {1: {'foo': 'bar'}}

Required dictionary keys
````````````````````````

By default, keys in the schema are not required to be in the data::

    >>> schema = Schema({1: 2, 3: 4})
    >>> schema({3: 4})
    {3: 4}

Similarly to how ``extra_`` keys work, this behaviour can be overridden
per-schema::

    >>> schema = Schema({1: 2, 3: 4}, required=True)
    >>> try:
    ...   schema({3: 4})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "required key not provided @ data[1]"
    True

And per-key, with the marker token ``Required(key)``::

    >>> schema = Schema({Required(1): 2, 3: 4})
    >>> try:
    ...   schema({3: 4})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "required key not provided @ data[1]"
    True
    >>> schema({1: 2})
    {1: 2}

Optional dictionary keys
````````````````````````

If a schema has ``required=True``, keys may be individually marked as
optional using the marker token ``Optional(key)``::

    >>> from voluptuous import Optional
    >>> schema = Schema({1: 2, Optional(3): 4}, required=True)
    >>> try:
    ...   schema({})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "required key not provided @ data[1]"
    True
    >>> schema({1: 2})
    {1: 2}
    >>> try:
    ...   schema({1: 2, 4: 5})
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "extra keys not allowed @ data[4]"
    True

::

    >>> schema({1: 2, 3: 4})
    {1: 2, 3: 4}

Objects
-------

Each key-value pair in a schema dictionary is validated against each
attribute-value pair in the corresponding object::

    >>> from voluptuous import Object
    >>> class Structure(object):
    ...     def __init__(self, q=None):
    ...         self.q = q
    ...     def __repr__(self):
    ...         return '<Structure(q={0.q!r})>'.format(self)
    ...
    >>> schema = Schema(Object({'q': 'one'}, cls=Structure))
    >>> schema(Structure(q='one'))
    <Structure(q='one')>

Error reporting
---------------

Validators must throw an ``Invalid`` exception if invalid data is passed
to them. All other exceptions are treated as errors in the validator and
will not be caught.

Each ``Invalid`` exception has an associated ``path`` attribute representing
the path in the data structure to our currently validating value, as well
as an ``error_message`` attribute that contains the message of the original
exception. This is especially useful when you want to catch ``Invalid``
exceptions and give some feedback to the user, for instance in the context of
an HTTP API.

::

    >>> def validate_email(email):
    ...     """Validate email."""
    ...     if not "@" in email:
    ...         raise Invalid("This email is invalid.")
    ...     return email
    >>> schema = Schema({"email": validate_email})
    >>> exc = None
    >>> try:
    ...     schema({"email": "whatever"})
    ... except MultipleInvalid as e:
    ...     exc = e
    >>> str(exc)
    "This email is invalid. for dictionary value @ data['email']"
    >>> exc.path
    ['email']
    >>> exc.msg
    'This email is invalid.'
    >>> exc.error_message
    'This email is invalid.'

The ``path`` attribute is used during error reporting, but also during matching
to determine whether an error should be reported to the user or if the next
match should be attempted. This is determined by comparing the depth of the
path where the check is, to the depth of the path where the error occurred. If
the error is more than one level deeper, it is reported.

The upshot of this is that *matching is depth-first and fail-fast*.

To illustrate this, here is an example schema::

    >>> schema = Schema([[2, 3], 6])

Each value in the top-level list is matched depth-first in-order. Given
input data of ``[[6]]``, the inner list will match the first element of
the schema, but the literal ``6`` will not match any of the elements of
that list. This error will be reported back to the user immediately. No
backtracking is attempted::

    >>> try:
    ...   schema([[6]])
    ...   raise AssertionError('MultipleInvalid not raised')
    ... except MultipleInvalid as e:
    ...   exc = e
    >>> str(exc) == "invalid list value @ data[0][0]"
    True

If we pass the data ``[6]``, the ``6`` is not a list type and so will not
recurse into the first element of the schema. Matching will continue on
to the second element in the schema, and succeed:

    >>> schema([6])
    [6]

Running tests.
--------------

Voluptuous is using nosetests::

    $ nosetests


Why use Voluptuous over another validation library?
---------------------------------------------------

Validators are simple callables.
    No need to subclass anything, just use a function.

Errors are simple exceptions.
    A validator can just ``raise Invalid(msg)`` and expect the user to get useful
    messages.

Schemas are basic Python data structures.
    Should your data be a dictionary of integer keys to strings? ``{int: str}``
    does what you expect. List of integers, floats or strings? ``[int, float,
    str]``.

Designed from the ground up for validating more than just forms.
    Nested data structures are treated in the same way as any other type. Need
    a list of dictionaries? ``[{}]``

Consistency.
    Types in the schema are checked as types. Values are compared as values.
    Callables are called to validate. Simple.

Other libraries and inspirations
--------------------------------

Voluptuous is heavily inspired by
`Validino <http://code.google.com/p/validino/>`_, and to a lesser extent,
`jsonvalidator <http://code.google.com/p/jsonvalidator/>`_ and
`json_schema <http://blog.sendapatch.se/category/json_schema.html>`_.

I greatly prefer the light-weight style promoted by these libraries to
the complexity of libraries like FormEncode.
