Error reporting should be accurate::

  >>> from voluptuous import *
  >>> schema = Schema(['one', {'two': 'three', 'four': ['five'],
  ...                          'six': {'seven': 'eight'}}])
  >>> schema(['one'])
  ['one']
  >>> schema([{'two': 'three'}])
  [{'two': 'three'}]

It should show the exact index and container type, in this case a list value::

  >>> schema(['one', 'two'])
  Traceback (most recent call last):
  ...
  InvalidList: invalid list value @ data[1]

It should also be accurate for nested values::

  >>> schema([{'two': 'nine'}])
  Traceback (most recent call last):
  ...
  InvalidList: not a valid value for dictionary value @ data[0]['two']
  >>> schema([{'four': ['nine']}])
  Traceback (most recent call last):
  ...
  InvalidList: invalid list value @ data[0]['four'][0]
  >>> schema([{'six': {'seven': 'nine'}}])
  Traceback (most recent call last):
  ...
  InvalidList: not a valid value for dictionary value @ data[0]['six']['seven']

Errors should be reported depth-first::

  >>> validate = Schema({'one': {'two': 'three', 'four': 'five'}})
  >>> try:
  ...   validate({'one': {'four': 'six'}})
  ... except Invalid, e:
  ...   print e
  ...   print e.path
  not a valid value for dictionary value @ data['one']['four']
  ['one', 'four']

Voluptuous supports validation when extra fields are present in the data::

  >>> schema = Schema({'one': 1, extra: object})
  >>> schema({'two': 'two', 'one': 2})
  {'two': 'two', 'one': 2}
  >>> schema = Schema({'one': 1})
  >>> schema({'two': 2})
  Traceback (most recent call last):
  ...
  InvalidList: extra keys not allowed @ data['two']


dict, list, and tuple should be available as type validators::

  >>> Schema(dict)({'a': 1, 'b': 2})
  {'a': 1, 'b': 2}
  >>> Schema(list)([1,2,3])
  [1, 2, 3]
  >>> Schema(tuple)((1,2,3))
  (1, 2, 3)
  

Validation should return instances of the right types when the types are
subclasses of dict or list::

  >>> class Dict(dict):
  ...   pass
  >>>
  >>> d = Schema(dict)(Dict(a=1, b=2))
  >>> d
  {'a': 1, 'b': 2}
  >>> type(d) is Dict
  True
  >>> class List(list):
  ...   pass    
  >>>
  >>> l = Schema(list)(List([1,2,3]))
  >>> l
  [1, 2, 3]
  >>> type(l) is List
  True

Multiple errors are reported::

  >>> schema = Schema({'one': 1, 'two': 2})
  >>> try:
  ...   schema({'one': 2, 'two': 3, 'three': 4})
  ... except InvalidList, e:
  ...   errors = sorted(e.errors, key=lambda k: str(k))
  ...   print [str(i) for i in errors]  # doctest: +NORMALIZE_WHITESPACE
  ["extra keys not allowed @ data['three']",
   "not a valid value for dictionary value @ data['one']",
   "not a valid value for dictionary value @ data['two']"]
  >>> schema = Schema([[1], [2], [3]])
  >>> try:
  ...   schema([1, 2, 3])
  ... except InvalidList, e:
  ...   print [str(i) for i in e.errors]  # doctest: +NORMALIZE_WHITESPACE
  ['invalid list value @ data[0]',
   'invalid list value @ data[1]',
   'invalid list value @ data[2]']

Custom classes validate as schemas::

    >>> class Thing(object):
    ...     pass
    >>> schema = Schema(Thing)
    >>> t = schema(Thing())
    >>> type(t) is Thing
    True

Classes with custom metaclasses should validate as schemas::

    >>> class MyMeta(type):
    ...     pass
    >>> class Thing(object):
    ...     __metaclass__ = MyMeta
    >>> schema = Schema(Thing)
    >>> t = schema(Thing())
    >>> type(t) is Thing
    True
