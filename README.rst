Voluptuous, despite the name, is a Python data validation library.

A schema like this:

    >>> import voluptuous as V
    >>> settings = {
    ...   'snmp_community': str,
    ...   'retries': int,
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

Is validated like so:

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
