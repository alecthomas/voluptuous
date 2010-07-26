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
  Invalid: invalid list value @ data[1]

It should also be accurate for nested values::

  >>> schema([{'two': 'nine'}])
  Traceback (most recent call last):
  ...
  Invalid: not a valid value for dictionary value @ data[0]['two']
  >>> schema([{'four': ['nine']}])
  Traceback (most recent call last):
  ...
  Invalid: invalid list value @ data[0]['four'][0]
  >>> schema([{'six': {'seven': 'nine'}}])
  Traceback (most recent call last):
  ...
  Invalid: not a valid value for dictionary value @ data[0]['six']['seven']

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

  >>> extra = None
  >>> schema = Schema({'one': 1, extra: object})
  >>> schema({'two': 'two', 'one': 2})
  {'two': 'two', 'one': 2}
  >>> schema = Schema({'one': 1})
  >>> schema({'two': 2})
  Traceback (most recent call last):
  ...
  Invalid: not a valid value for dictionary key @ data['two']

