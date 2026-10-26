"""Coverage for humanize helpers, util transforms and error classes.

Probed behaviours pinned here:

* ``humanize_error`` renders ``"<msg> @ data['a']. Got <value>"`` and
  nests paths with ``['b']`` segments; with no path it omits the
  ``@ data`` part entirely.
* ``validate_with_humanized_errors`` raises a plain ``Error`` whose
  message is the humanized text (not a ``MultipleInvalid``).
* The ``util`` transforms (``Lower``/``Upper``/``Capitalize``/``Title``/
  ``Strip``) are plain callables used as ``Schema(Lower)``, not as
  ``Lower()`` instances.
"""

import pytest

from voluptuous import (
    Invalid,
    MultipleInvalid,
    Schema,
)
from voluptuous.error import (
    CoerceInvalid,
    DictInvalid,
    Error,
    MultipleInvalid as Multi,
    RequiredFieldInvalid,
    TypeInvalid,
)
from voluptuous.humanize import (
    humanize_error,
    validate_with_humanized_errors,
)
from voluptuous.util import (
    Capitalize,
    DefaultTo,
    Literal,
    Lower,
    Set,
    SetTo,
    Strip,
    Title,
    Upper,
)


# ---------------------------------------------------------------- humanize

def test_humanize_error_single_path():
    assert humanize_error({"a": "bad"}, Invalid("bad value", path=["a"])) == (
        "bad value @ data['a']. Got 'bad'"
    )


def test_humanize_error_nested_path():
    assert humanize_error({"a": {"b": 1}}, Invalid("x", path=["a", "b"])) == (
        "x @ data['a']['b']. Got 1"
    )


def test_humanize_error_no_path_omits_data_part():
    assert humanize_error({"a": 1}, Invalid("oops")) == "oops. Got {'a': 1}"


def test_humanize_error_list_index_path():
    assert humanize_error([10, 20], Invalid("bad", path=[1])) == "bad @ data[1]. Got 20"


def test_validate_with_humanized_errors_passes_valid_data():
    assert validate_with_humanized_errors({"a": 1}, Schema({"a": int})) == {"a": 1}


def test_validate_with_humanized_errors_humanizes_message():
    # It raises a plain Error (not MultipleInvalid) carrying the
    # humanized text, e.g. "... @ data['a']. Got 'x'".
    with pytest.raises(Error) as exc:
        validate_with_humanized_errors({"a": "x"}, Schema({"a": int}))
    assert "data['a']" in str(exc.value)
    assert "Got 'x'" in str(exc.value)


# ---------------------------------------------------------------- util transforms

@pytest.mark.parametrize(
    "fn, value, expected",
    [
        (Lower, "ABC", "abc"),
        (Upper, "abc", "ABC"),
        (Capitalize, "hello world", "Hello world"),
        (Title, "hello world", "Hello World"),
        (Strip, "  hi  ", "hi"),
    ],
)
def test_util_transforms_as_schema_callables(fn, value, expected):
    assert Schema(fn)(value) == expected


def test_util_transforms_are_plain_functions():
    assert Lower("MiXeD") == "mixed"
    assert Strip("\t padded \n") == "padded"


def test_default_to_replaces_none_only():
    assert Schema(DefaultTo(7))(None) == 7
    assert Schema(DefaultTo(7))(0) == 0
    assert Schema(DefaultTo(7))("") == ""


def test_set_to_always_returns_its_value():
    # Unlike DefaultTo, SetTo ignores the input entirely.
    assert Schema(SetTo(9))(None) == 9
    assert Schema(SetTo(9))(3) == 9
    assert Schema(SetTo(9))("anything") == 9


def test_set_validator_converts_lists_to_sets():
    # Set() takes no collection argument; it converts its input.
    assert Schema(Set())([1, 2]) == {1, 2}
    assert Schema(Set())({1, 2}) == {1, 2}
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Set())([{1}, {2}])
    assert "cannot be presented as set" in exc.value.errors[0].error_message


def test_literal_validator():
    assert Schema(Literal("x"))("x") == "x"
    with pytest.raises(MultipleInvalid):
        Schema(Literal("x"))("y")


# ---------------------------------------------------------------- error classes

def test_invalid_attributes():
    err = Invalid("oops", path=["a"], error_message="custom", error_type="t")
    assert err.path == ["a"]
    assert err.error_message == "custom"
    assert err.error_type == "t"
    # str() appends " for <error_type>" and the path.
    assert str(err) == "oops for t @ data['a']"


def test_error_hierarchy():
    assert issubclass(TypeInvalid, Invalid)
    assert issubclass(RequiredFieldInvalid, Invalid)
    assert issubclass(DictInvalid, Invalid)
    assert issubclass(CoerceInvalid, Invalid)
    assert issubclass(Multi, Invalid)
    assert issubclass(Error, Exception)


def test_multiple_invalid_str_shows_first_error_only():
    err = MultipleInvalid([Invalid("one", path=["a"]), Invalid("two", path=["b"])])
    assert str(err) == "one @ data['a']"
    assert len(err.errors) == 2


def test_schema_error_is_distinct_from_invalid():
    from voluptuous.error import SchemaError

    assert issubclass(SchemaError, Error)
    assert not issubclass(SchemaError, Invalid)
