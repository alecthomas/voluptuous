import copy
from nose.tools import assert_equal, with_setup

import voluptuous
from voluptuous import (
    Schema, Required, Extra, Invalid, In, Remove, Literal,
    Url, MultipleInvalid, LiteralInvalid
)


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


def test_remove():
    """Verify that Remove works."""
    # remove dict keys
    schema = Schema({"weight": int,
                     Remove("color"): str,
                     Remove("amount"): int})
    out_ = schema({"weight": 10, "color": "red", "amount": 1})
    assert "color" not in out_ and "amount" not in out_

    # remove keys by type
    schema = Schema({"weight": float,
                     "amount": int,
                     # remvove str keys with int values
                     Remove(str): int,
                     # keep str keys with str values
                     str: str})
    out_ = schema({"weight": 73.4,
                   "condition": "new",
                   "amount": 5,
                   "left": 2})
    # amount should stay since it's defined
    # other string keys with int values will be removed
    assert "amount" in out_ and "left" not in out_
    # string keys with string values will stay
    assert "condition" in out_

    # remove value from list
    schema = Schema([Remove(1), int])
    out_ = schema([1, 2, 3, 4, 1, 5, 6, 1, 1, 1])
    assert_equal(out_, [2, 3, 4, 5, 6])

    # remove values from list by type
    schema = Schema([1.0, Remove(float), int])
    out_ = schema([1, 2, 1.0, 2.0, 3.0, 4])
    assert_equal(out_, [1, 2, 1.0, 4])


def test_extra_empty_errors():
    schema = Schema({'a': {Extra: object}}, required=True)
    schema({'a': {}})


def test_literal():
    """ test with Literal """

    schema = Schema([Literal({"a": 1}), Literal({"b": 1})])
    schema([{"a": 1}])
    schema([{"b": 1}])
    schema([{"a": 1}, {"b": 1}])

    try:
        schema([{"c": 1}])
    except Invalid as e:
        assert_equal(str(e), 'invalid list value @ data[0]')
    else:
        assert False, "Did not raise Invalid"

    schema = Schema(Literal({"a": 1}))
    try:
        schema({"b": 1})
    except MultipleInvalid as e:
        assert_equal(str(e), "{'b': 1} not match for {'a': 1}")
        assert_equal(len(e.errors), 1)
        assert_equal(type(e.errors[0]), LiteralInvalid)
    else:
        assert False, "Did not raise Invalid"


def test_url_validation():
    """ test with valid URL """
    schema = Schema({"url": Url()})
    out_ = schema({"url": "http://example.com/"})

    assert 'http://example.com/', out_.get("url")


def test_url_validation_with_none():
    """ test with invalid None url"""
    schema = Schema({"url": Url()})
    try:
        schema({"url": None})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for None url"


def test_url_validation_with_empty_string():
    """ test with empty string URL """
    schema = Schema({"url": Url()})
    try:
        schema({"url": ''})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for empty string url"


def test_url_validation_without_host():
    """ test with empty host URL """
    schema = Schema({"url": Url()})
    try:
        schema({"url": 'http://'})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for empty string url"


def test_copy_dict_undefined():
    """ test with a copied dictionary """
    fields = {
        Required("foo"): int
    }
    copied_fields = copy.deepcopy(fields)

    schema = Schema(copied_fields)

    # This used to raise a `TypeError` because the instance of `Undefined`
    # was a copy, so object comparison would not work correctly.
    try:
        schema({"foo": "bar"})
    except Exception as e:
        assert isinstance(e, MultipleInvalid)


def test_sorting():
    """ Expect alphabetic sorting """
    foo = Required('foo')
    bar = Required('bar')
    items = [foo, bar]
    expected = [bar, foo]
    result = sorted(items)
    assert result == expected


def test_schema_extend():
    """Verify that Schema.extend copies schema keys from both."""

    base = Schema({'a': int}, required=True)
    extension = {'b': str}
    extended = base.extend(extension)

    assert base.schema == {'a': int}
    assert extension == {'b': str}
    assert extended.schema == {'a': int, 'b': str}
    assert extended.required == base.required
    assert extended.extra == base.extra


def test_schema_extend_overrides():
    """Verify that Schema.extend can override required/extra parameters."""

    base = Schema({'a': int}, required=True)
    extended = base.extend({'b': str}, required=False, extra=voluptuous.ALLOW_EXTRA)

    assert base.required == True
    assert base.extra == voluptuous.PREVENT_EXTRA
    assert extended.required == False
    assert extended.extra == voluptuous.ALLOW_EXTRA


def restore_schema_defaults():
    Schema.DEFAULT_REQUIRED = False
    Schema.DEFAULT_EXTRA = voluptuous.PREVENT_EXTRA


@with_setup(teardown=restore_schema_defaults)
def test_schema_default_parameters():
    """Schema default parameters can be changed"""

    schema = Schema(1)
    assert schema.required == False
    assert schema.extra == voluptuous.PREVENT_EXTRA

    Schema.DEFAULT_REQUIRED = True
    Schema.DEFAULT_EXTRA = voluptuous.REMOVE_EXTRA

    schema = Schema(1)
    assert schema.required == True
    assert schema.extra == voluptuous.REMOVE_EXTRA
