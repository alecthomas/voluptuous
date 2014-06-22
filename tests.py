from nose.tools import assert_equal

import voluptuous
from voluptuous import Schema, Required, Extra, Invalid, In, All


def test_required():
    """Verify that Required works."""
    schema = Schema({Required('q'): 1})
    # Can't use nose's raises (because we need to access the raised
    # exception, nor assert_raises which fails with Python 2.6.9.
    try:
        schema({})
    except Invalid as e:
        assert_equal(str(e), "required key not provided @ data['q']")
    else:
        assert False, "Did not raise Invalid"


def test_extra_with_required():
    """Verify that Required does not break Extra."""
    schema = Schema({Required('toaster'): str, Extra: object})
    r = schema({'toaster': 'blue', 'another_valid_key': 'another_valid_value'})
    assert_equal(
        r, {'toaster': 'blue', 'another_valid_key': 'another_valid_value'})


def test_iterate_candidates():
    """Verify that the order for iterating over mapping candidates is right."""
    schema = {
        "toaster": str,
        Extra: object,
    }
    # toaster should be first.
    assert_equal(voluptuous._iterate_mapping_candidates(schema)[0][0],
                 'toaster')


def test_in():
    """Verify that In works."""
    schema = Schema({"color": In(frozenset(["blue", "red", "yellow"]))})
    schema({"color": "blue"})


def test_bool_literal():
    """ Verify that True and False can be used in schemas, and bool works """
    tests = {
        True: {
            'valid': [True, 1],
            'invalid': [False],
            'error': ['not a valid value'],
        },
        False: {
            'valid': [False, 0],
            'invalid': [True],
            'error': ['not a valid value'],
        },
        bool: {
            'valid': [True, False],
            'invalid': [1, 0, '', 'true'],
            'error': ['expected bool'],
        },
        All(True, bool): {
            'valid': [True],
            'invalid': [False, 1],
            'error': ['not a valid value', 'expected bool'],
        },
        All(False, bool): {
            'valid': [False],
            'invalid': [True, 0],
            'error': ['not a valid value', 'expected bool'],
        },
    }

    for s, data in tests.items():
        schema = Schema(s)
        for v in data['valid']:
            schema(v)
        for i, v in enumerate(data['invalid']):
            try:
                schema(v)
            except Invalid as e:
                assert_equal(str(e), data['error'][i % len(data['error'])])
            else:
                err = "Schema({})({}) Did not raise Invalid"
                assert False, err.format(s, v)
