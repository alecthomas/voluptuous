import copy
from nose.tools import assert_equal, assert_raises

from voluptuous import (
    Schema, Required, Extra, Invalid, In, Remove, Literal,
    Url, MultipleInvalid, LiteralInvalid, NotIn, Match, Email,
    Replace, Range, Coerce, All, Any, Length, FqdnUrl, ALLOW_EXTRA, PREVENT_EXTRA,
    validate_schema,
)
from voluptuous.humanize import humanize_error


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
    from voluptuous.schema_builder import _iterate_mapping_candidates
    assert_equal(_iterate_mapping_candidates(schema)[0][0], 'toaster')


def test_in():
    """Verify that In works."""
    schema = Schema({"color": In(frozenset(["blue", "red", "yellow"]))})
    schema({"color": "blue"})


def test_not_in():
    """Verify that NotIn works."""
    schema = Schema({"color": NotIn(frozenset(["blue", "red", "yellow"]))})
    schema({"color": "orange"})
    try:
        schema({"color": "blue"})
    except Invalid as e:
        assert_equal(str(e), "value is not allowed for dictionary value @ data['color']")
    else:
        assert False, "Did not raise NotInInvalid"


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
        assert_equal(str(e), "{'c': 1} not match for {'b': 1} @ data[0]")
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


def test_email_validation():
    """ test with valid email """
    schema = Schema({"email": Email()})
    out_ = schema({"email": "example@example.com"})

    assert 'example@example.com"', out_.get("url")


def test_email_validation_with_none():
    """ test with invalid None Email"""
    schema = Schema({"email": Email()})
    try:
        schema({"email": None})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected an Email for dictionary value @ data['email']")
    else:
        assert False, "Did not raise Invalid for None url"


def test_email_validation_with_empty_string():
    """ test with empty string Email"""
    schema = Schema({"email": Email()})
    try:
        schema({"email": ''})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected an Email for dictionary value @ data['email']")
    else:
        assert False, "Did not raise Invalid for empty string url"


def test_email_validation_without_host():
    """ test with empty host name in email """
    schema = Schema({"email": Email()})
    try:
        schema({"email": 'a@.com'})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected an Email for dictionary value @ data['email']")
    else:
        assert False, "Did not raise Invalid for empty string url"


def test_fqdn_url_validation():
    """ test with valid fully qualified domain name url """
    schema = Schema({"url": FqdnUrl()})
    out_ = schema({"url": "http://example.com/"})

    assert 'http://example.com/', out_.get("url")


def test_fqdn_url_without_domain_name():
    """ test with invalid fully qualified domain name url """
    schema = Schema({"url": FqdnUrl()})
    try:
        schema({"url": "http://localhost/"})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a Fully qualified domain name URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for None url"


def test_fqdnurl_validation_with_none():
    """ test with invalid None FQDN url"""
    schema = Schema({"url": FqdnUrl()})
    try:
        schema({"url": None})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a Fully qualified domain name URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for None url"


def test_fqdnurl_validation_with_empty_string():
    """ test with empty string FQDN URL """
    schema = Schema({"url": FqdnUrl()})
    try:
        schema({"url": ''})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a Fully qualified domain name URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for empty string url"


def test_fqdnurl_validation_without_host():
    """ test with empty host FQDN URL """
    schema = Schema({"url": FqdnUrl()})
    try:
        schema({"url": 'http://'})
    except MultipleInvalid as e:
        assert_equal(str(e),
                     "expected a Fully qualified domain name URL for dictionary value @ data['url']")
    else:
        assert False, "Did not raise Invalid for empty string url"


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
    extended = base.extend({'b': str}, required=False, extra=ALLOW_EXTRA)

    assert base.required is True
    assert base.extra == PREVENT_EXTRA
    assert extended.required is False
    assert extended.extra == ALLOW_EXTRA


def test_repr():
    """Verify that __repr__ returns valid Python expressions"""
    match = Match('a pattern', msg='message')
    replace = Replace('you', 'I', msg='you and I')
    range_ = Range(min=0, max=42, min_included=False,
                   max_included=False, msg='number not in range')
    coerce_ = Coerce(int, msg="moo")
    all_ = All('10', Coerce(int), msg='all msg')

    assert_equal(repr(match), "Match('a pattern', msg='message')")
    assert_equal(repr(replace), "Replace('you', 'I', msg='you and I')")
    assert_equal(
        repr(range_),
        "Range(min=0, max=42, min_included=False, max_included=False, msg='number not in range')"
    )
    assert_equal(repr(coerce_), "Coerce(int, msg='moo')")
    assert_equal(repr(all_), "All('10', Coerce(int, msg=None), msg='all msg')")


def test_list_validation_messages():
    """ Make sure useful error messages are available """

    def is_even(value):
        if value % 2:
            raise Invalid('%i is not even' % value)
        return value

    schema = Schema(dict(even_numbers=[All(int, is_even)]))

    try:
        schema(dict(even_numbers=[3]))
    except Invalid as e:
        assert_equal(len(e.errors), 1, e.errors)
        assert_equal(str(e.errors[0]), "3 is not even @ data['even_numbers'][0]")
        assert_equal(str(e), "3 is not even @ data['even_numbers'][0]")
    else:
        assert False, "Did not raise Invalid"


def test_nested_multiple_validation_errors():
    """ Make sure useful error messages are available """

    def is_even(value):
        if value % 2:
            raise Invalid('%i is not even' % value)
        return value

    schema = Schema(dict(even_numbers=All([All(int, is_even)],
                                          Length(min=1))))

    try:
        schema(dict(even_numbers=[3]))
    except Invalid as e:
        assert_equal(len(e.errors), 1, e.errors)
        assert_equal(str(e.errors[0]), "3 is not even @ data['even_numbers'][0]")
        assert_equal(str(e), "3 is not even @ data['even_numbers'][0]")
    else:
        assert False, "Did not raise Invalid"


def test_humanize_error():
    data = {
        'a': 'not an int',
        'b': [123]
    }
    schema = Schema({
        'a': int,
        'b': [str]
    })
    try:
        schema(data)
    except MultipleInvalid as e:
        assert_equal(
            humanize_error(data, e),
            "expected int for dictionary value @ data['a']. Got 'not an int'\n"
            "expected str @ data['b'][0]. Got 123"
        )
    else:
        assert False, 'Did not raise MultipleInvalid'


def test_fix_157():
    s = Schema(All([Any('one', 'two', 'three')]), Length(min=1))
    assert_equal(['one'], s(['one']))
    assert_raises(MultipleInvalid, s, ['four'])


def test_schema_decorator():
    @validate_schema(int)
    def fn(arg):
        return arg

    fn(1)
    assert_raises(Invalid, fn, 1.0)
