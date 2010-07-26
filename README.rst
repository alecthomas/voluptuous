Voluptuous is a Python data validation library
==============================================
Voluptuous, *despite* the name, is a Python data validation library. It is
primarily intended for validating data coming into Python from JSON, YAML, etc.

It has three goals:

1. Simplicity.
2. Support complex data structures.
3. Provide useful error messages.

Show me an example
------------------
If we were trying to implement Twitter's `user search API
<http://apiwiki.twitter.com/Twitter-REST-API-Method:-users-search>_` we might
use a schema like this:

  >>> from voluptuous import Schema, required, all, length, range
  >>> schema = Schema({
  ...   required('q'): all(str, length(min=1)),
  ...   'per_page': all(int, range(max=20)),
  ...   'page': int,
  ... })

This schema enforces the interface defined in Twitter's documentation.
"per_page" is an integer no greater than 20. "page" is an integer.

  >>> schema({'q': ''})
  Traceback (most recent call last):
  ...
  Invalid: length of value is too short for dictionary value @ data['q']
  

Why Voluptuous over another validation library?
-----------------------------------------------
Most existing Python validation libraries are oriented towards validating HTML
forms. Voluptuous can be used for this case, but is primarily intended for
validating complex data structures, such as for REST API calls.

Not all libraries are tied to form validation. Some, such as `Validino
<http://code.google.com/p/validino/>_`, support arbitrary data structures, but
have other issues.

Defining schemas
----------------
Schemas are nested data structures consisting of dictionaries, lists and
scalars. Each node in the input schema is pattern matched against corresponding
nodes in the input data.

Here is an example schema:

  >>> import voluptuous as V
  >>> settings = {
  ...   'snmp_community': V.coerce(str),
  ...   'retries': V.coerce(int),
  ...   'snmp_version': V.all(V.coerce(str), V.any('3', '2c', '1')),
  ... }
  >>> features = ['Ping', 'Uptime', 'Http']
  >>> schema = V.Schema({
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

And the data to be validated (with invalid data at set/retries):

  >>> data = {
  ...   'set': {
  ...     'snmp_community': 'public',
  ...     'snmp_version': '2c',
  ...     'retries': 'one',
  ...   },
  ...   'targets': {
  ...     'exclude': ['Ping'],
  ...     'features': {
  ...       'Uptime': {'retries': 3},
  ...       'Users': {'snmp_community': 'monkey'},
  ...     },
  ...   },
  ... }

And finally, validation:

  >>> schema(data)  # doctest: +NORMALIZE_WHITESPACE
  Traceback (most recent call last):
  ...
  Invalid: expected int for dictionary value @ data['set']['retries']

Correct the invalid data and revalidate:

  >>> data['set']['retries'] = 1
  >>> schema(data)  # doctest: +NORMALIZE_WHITESPACE
  {'set': {'snmp_version': '2c', 'snmp_community': 'public', 'retries': 1},
    'targets': {'exclude': ['Ping'],
                'features': {'Uptime': {'retries': 3},
                            'Users': {'snmp_community': 'monkey'}}}}
