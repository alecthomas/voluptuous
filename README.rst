Voluptuous, *despite* the name, is a Python data validation library.

Voluptuous has two goals:

1. Support complex data structures.
2. Provide useful error messages.

Schemas are defined as simple Python nested data structures consisting of
dictionaries, lists and scalars. Each node in the input schema is pattern
matched against corresponding nodes in the input data.

Here's an example schema:

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
