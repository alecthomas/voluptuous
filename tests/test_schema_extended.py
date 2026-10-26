"""Extended Schema / marker coverage for voluptuous.

Probed behaviours pinned here:

* ``Schema`` wraps every failure in ``MultipleInvalid``; the
  per-error attributes (``path``, ``error_message``, ``error_type``)
  are what callers actually inspect.
* ``Object`` schemas work on attributes, not dict keys: passing a
  dict yields ``{}`` rather than a validation error.
* ``message``-decorated validators must be *called* (``isint()``) to
  become a validator; the undecorated function itself is not one.
"""

import types

import pytest

from voluptuous import (
    ALLOW_EXTRA,
    PREVENT_EXTRA,
    REMOVE_EXTRA,
    Exclusive,
    Inclusive,
    Invalid,
    Marker,
    Msg,
    MultipleInvalid,
    Object,
    Optional,
    Remove,
    Required,
    Schema,
    default_factory,
)
from voluptuous.schema_builder import message


def invalid(schema, value):
    with pytest.raises(MultipleInvalid):
        schema(value)


# ---------------------------------------------------------------- basic shapes

def test_scalar_type_schema():
    assert Schema(int)(5) == 5
    invalid(Schema(int), "x")


def test_literal_value_schema():
    assert Schema("hello")("hello") == "hello"
    invalid(Schema("hello"), "bye")


def test_list_schema_and_error_path():
    assert Schema([int])([1, 2, 3]) == [1, 2, 3]
    with pytest.raises(MultipleInvalid) as exc:
        Schema([int])([1, "x"])
    assert exc.value.errors[0].path == [1]


def test_tuple_schema():
    assert Schema((int, str))((1, "a")) == (1, "a")


def test_set_schema():
    assert Schema({int})({1, 2}) == {1, 2}


def test_type_key_schema_validates_all_values():
    assert Schema({str: int})({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    invalid(Schema({str: int}), {"a": "x"})


def test_nested_schema_error_path():
    with pytest.raises(MultipleInvalid) as exc:
        Schema({"a": {"b": int}})({"a": {"b": "x"}})
    assert exc.value.errors[0].path == ["a", "b"]


def test_multiple_errors_collected():
    with pytest.raises(MultipleInvalid) as exc:
        Schema({"a": int, "b": int})({"a": "x", "b": "y"})
    assert len(exc.value.errors) == 2


def test_error_type_attribute():
    # For a dict value, error_type names the context ("dictionary
    # value") while error_message carries the validator's message.
    with pytest.raises(MultipleInvalid) as exc:
        Schema({"a": int})({"a": "x"})
    assert exc.value.errors[0].error_type == "dictionary value"
    assert exc.value.errors[0].error_message == "expected int"


# ---------------------------------------------------------------- markers

def test_required_missing_message_and_path():
    with pytest.raises(MultipleInvalid) as exc:
        Schema({Required("a"): int})({})
    err = exc.value.errors[0]
    assert err.path == ["a"]
    assert err.error_message == "required key not provided"


def test_required_with_value_default_and_callable_default():
    assert Schema({Required("a", default=9): int})({}) == {"a": 9}
    assert Schema({Required("a", default=lambda: 3): int})({}) == {"a": 3}


def test_optional_default_and_default_factory():
    assert Schema({Optional("a", default=5): int})({}) == {"a": 5}
    assert Schema({Optional("a", default=default_factory(list)): list})({}) == {"a": []}


def test_schema_required_flag_makes_plain_keys_required():
    invalid(Schema({"a": int}, required=True), {})
    assert Schema({"a": int}, required=True)({"a": 1}) == {"a": 1}


def test_extra_prevent_is_default():
    invalid(Schema({"a": int}), {"a": 1, "b": 2})
    invalid(Schema({"a": int}, extra=PREVENT_EXTRA), {"a": 1, "b": 2})


def test_extra_allow_keeps_unknown_keys():
    assert Schema({"a": int}, extra=ALLOW_EXTRA)({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_extra_remove_drops_unknown_keys():
    assert Schema({"a": int}, extra=REMOVE_EXTRA)({"a": 1, "b": 2}) == {"a": 1}


def test_extra_error_path_and_message():
    with pytest.raises(MultipleInvalid) as exc:
        Schema({"a": int})({"a": 1, "b": 2})
    err = exc.value.errors[0]
    assert err.path == ["b"]
    assert err.error_message == "extra keys not allowed"


def test_exclusive_group_rejects_two_members():
    schema = Schema({Exclusive("a", "grp"): int, Exclusive("b", "grp"): int})
    assert schema({"a": 1}) == {"a": 1}
    with pytest.raises(MultipleInvalid) as exc:
        schema({"a": 1, "b": 2})
    assert "exclusion" in exc.value.errors[0].error_message


def test_inclusive_group_requires_all_members():
    schema = Schema({Inclusive("a", "grp"): int, Inclusive("b", "grp"): int})
    assert schema({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    with pytest.raises(MultipleInvalid) as exc:
        schema({"a": 1})
    assert "inclusion" in exc.value.errors[0].error_message


def test_remove_marker_drops_key():
    assert Schema({Remove("secret"): str, "a": int})({"secret": "x", "a": 1}) == {"a": 1}


def test_msg_overrides_error_message():
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Msg(int, "must be int"))("x")
    assert exc.value.errors[0].error_message == "must be int"


def test_message_decorator_must_be_called():
    @message("must be positive")
    def pos(v):
        if v <= 0:
            raise ValueError("neg")
        return v

    assert Schema(pos())(5) == 5
    with pytest.raises(MultipleInvalid) as exc:
        Schema(pos())(-1)
    assert exc.value.errors[0].error_message == "must be positive"


def test_object_schema_reads_attributes():
    obj = types.SimpleNamespace(a=1)
    result = Schema(Object({"a": int}))(obj)
    # Object validation rebuilds the object via type(data)(**out), so
    # the result is a copy with the same attributes, not the input.
    assert isinstance(result, types.SimpleNamespace)
    assert result is not obj
    assert result.a == 1
    # A dict is not an attribute bag: it validates to an empty mapping.
    assert Schema(Object({"a": int}))({"a": 1}) == {}


def test_schema_extend_adds_keys():
    extended = Schema({"a": int}).extend({"b": str})
    assert extended({"a": 1, "b": "x"}) == {"a": 1, "b": "x"}
    # Plain keys stay optional after extend; a wrong-typed value fails.
    assert extended({"a": 1}) == {"a": 1}
    invalid(extended, {"a": 1, "b": 5})


def test_schema_infer_from_dict_and_list():
    inferred = Schema.infer({"a": 1, "b": "x"})
    assert inferred({"a": 2, "b": "y"}) == {"a": 2, "b": "y"}
    invalid(inferred, {"a": "x", "b": "y"})
    assert Schema.infer([1, 2])([3, 4]) == [3, 4]


def test_schema_str_and_repr():
    assert str(Schema({"a": int})) == "{'a': <class 'int'>}"
    assert "Schema" in repr(Schema({"a": int}))


def test_validate_decorator_validates_function_arguments():
    from voluptuous.schema_builder import validate

    @validate({"a": int})
    def func(a):
        return a

    assert func({"a": 1}) == {"a": 1}
    with pytest.raises(MultipleInvalid):
        func({"a": "x"})


def test_marker_equality_and_str():
    assert Required("a") == Required("a")
    # Marker equality is by key only: Required and Optional with the
    # same key compare equal.
    assert Required("a") == Optional("a")
    assert Required("a") != Required("b")
    assert str(Required("a")) == "a"
    assert isinstance(Marker("a"), Marker)
