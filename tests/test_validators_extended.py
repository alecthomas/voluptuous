"""Extended validator coverage for voluptuous.

All expected values and messages below were probed against the shipped
implementation first. Two behaviours worth pinning explicitly:

* ``Number``'s ``precision`` counts *all* digits (``"1234.01"`` has
  precision 6, scale 2); ``precision=2`` therefore rejects ``"3.14"``,
  whose digit count is 3.
* ``Any`` failure reporting surfaces the first sub-validator's message
  (``"expected int"`` for ``Any(int, str)`` on a float), not a
  combined message -- tests assert the exception type, not that text.
"""

import pytest

from voluptuous import (
    All,
    Any,
    Boolean,
    Clamp,
    Coerce,
    Contains,
    Date,
    Datetime,
    Email,
    Equal,
    ExactSequence,
    FqdnUrl,
    In,
    IsFalse,
    IsTrue,
    Length,
    Match,
    Maybe,
    MultipleInvalid,
    NotIn,
    Number,
    Range,
    Replace,
    Schema,
    SomeOf,
    Union,
    Unique,
    Unordered,
    Url,
)


def invalid(schema, value):
    with pytest.raises(MultipleInvalid):
        schema(value)


# ---------------------------------------------------------------- Coerce

def test_coerce_int_from_string():
    assert Schema(Coerce(int))("42") == 42


def test_coerce_float_from_string():
    assert Schema(Coerce(float))("1.5") == 1.5


def test_coerce_list_from_string_splits_chars():
    assert Schema(Coerce(list))("abc") == ["a", "b", "c"]


def test_coerce_failure_message():
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Coerce(int))("abc")
    assert exc.value.errors[0].error_message == "expected int"


# ---------------------------------------------------------------- Range / Clamp

@pytest.mark.parametrize("value", [1, 5, 10])
def test_range_bounds_inclusive(value):
    assert Schema(Range(min=1, max=10))(value) == value


def test_range_below_min_message():
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Range(min=1, max=10))(0)
    assert "at least 1" in exc.value.errors[0].error_message


def test_range_above_max_message():
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Range(min=1, max=10))(11)
    assert "at most 10" in exc.value.errors[0].error_message


def test_range_min_only():
    assert Schema(Range(min=5))(10**9) == 10**9


def test_range_max_only():
    assert Schema(Range(max=5))(-10**9) == -10**9


def test_range_exclusive_bounds():
    invalid(Schema(Range(min=1, max=10, min_included=False)), 1)
    invalid(Schema(Range(min=1, max=10, max_included=False)), 10)
    assert Schema(Range(min=1, max=10, min_included=False, max_included=False))(5) == 5


def test_clamp_high_and_low():
    assert Schema(Clamp(min=1, max=10))(99) == 10
    assert Schema(Clamp(min=1, max=10))(-5) == 1
    assert Schema(Clamp(min=1, max=10))(5) == 5


def test_clamp_unorderable_value():
    invalid(Schema(Clamp(min=1, max=10)), "x")


# ---------------------------------------------------------------- Length / In / NotIn

def test_length_string_and_list():
    assert Schema(Length(min=2, max=4))("abc") == "abc"
    assert Schema(Length(min=1))([1]) == [1]


def test_length_too_short_and_too_long_messages():
    invalid(Schema(Length(min=2)), "a")
    invalid(Schema(Length(min=1, max=2)), [1, 2, 3])


@pytest.mark.parametrize("container", [["a", "b"], {"a": 1}, ("a", "b")])
def test_in_accepts_list_dict_tuple(container):
    assert Schema(In(container))("a") == "a"


def test_in_rejects_with_listing_message():
    with pytest.raises(MultipleInvalid) as exc:
        Schema(In(["a", "b"]))("c")
    assert "['a', 'b']" in exc.value.errors[0].error_message


def test_not_in():
    assert Schema(NotIn(["a"]))("b") == "b"
    invalid(Schema(NotIn(["a"])), "a")


# ---------------------------------------------------------------- sequence validators

def test_contains_substring_and_element():
    assert Schema(Contains("x"))("xyz") == "xyz"
    assert Schema(Contains(2))([1, 2]) == [1, 2]
    invalid(Schema(Contains("z")), "abc")


def test_exact_sequence_list_and_tuple():
    assert Schema(ExactSequence([int, str]))([1, "a"]) == [1, "a"]
    assert Schema(ExactSequence([int, str]))((1, "a")) == (1, "a")
    invalid(Schema(ExactSequence([int, str])), [1])
    invalid(Schema(ExactSequence([int, str])), [1, "a", 3])


def test_unique_ok_and_duplicate_message():
    assert Schema(Unique())([1, 2, 3]) == [1, 2, 3]
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Unique())([1, 1, 2])
    assert "duplicate" in exc.value.errors[0].error_message


def test_equal():
    assert Schema(Equal(5))(5) == 5
    with pytest.raises(MultipleInvalid) as exc:
        Schema(Equal(5))(6)
    assert "6 != target:5" in exc.value.errors[0].error_message


def test_unordered_accepts_any_order_and_rejects_duplicates_mismatch():
    assert Schema(Unordered([1, 2]))([2, 1]) == [2, 1]
    invalid(Schema(Unordered([1, 1, 2])), [1, 2, 2])


def test_some_of_min_and_max():
    assert Schema(SomeOf(min_valid=1, validators=[int, str]))(5) == 5
    assert Schema(SomeOf(min_valid=1, max_valid=1, validators=[int, str]))(5) == 5
    invalid(Schema(SomeOf(min_valid=2, validators=[int, str])), 5.5)


# ---------------------------------------------------------------- combinators

def test_any_accepts_either_and_rejects_neither():
    assert Schema(Any(int, str))("hi") == "hi"
    assert Schema(Any(int, str))(3) == 3
    invalid(Schema(Any(int, str)), 3.5)


def test_all_applies_in_order():
    assert Schema(All(Coerce(int), Range(min=0)))("7") == 7
    invalid(Schema(All(Coerce(int), Range(min=0))), "-5")
    invalid(Schema(All(str, Length(min=2))), "a")


def test_union_accepts_int_subclass_bool():
    # bool is an int subclass, so Union(int, str) accepts True.
    assert Schema(Union(int, str))(True) is True


def test_maybe_none_or_value():
    assert Schema(Maybe(int))(None) is None
    assert Schema(Maybe(int))(3) == 3
    invalid(Schema(Maybe(int)), "x")


# ---------------------------------------------------------------- text validators

def test_match_full_and_partial():
    assert Schema(Match(r"^\d+$"))("123") == "123"
    invalid(Schema(Match(r"^\d+$")), "abc")
    # Match is anchored at the start (re.match), not a search: a digit
    # prefix passes, but digits later in the string do not.
    assert Schema(Match(r"\d+"))("123abc") == "123abc"
    invalid(Schema(Match(r"\d+")), "abc123")


def test_replace_literal_and_regex():
    assert Schema(Replace("a", "b"))("aaa") == "bbb"
    assert Schema(Replace(r"\d", "X"))("a1b2") == "aXbX"


@pytest.mark.parametrize("good", ["a@b.com", "first.last+tag@sub.example.co.uk"])
def test_email_good(good):
    assert Schema(Email())(good) == good


def test_email_bad():
    invalid(Schema(Email()), "not-an-email")
    invalid(Schema(Email()), "a@b")


@pytest.mark.parametrize("good", ["https://example.com/x", "http://example.com:8080/p?q=1"])
def test_url_good(good):
    assert Schema(Url())(good) == good


def test_url_bad():
    invalid(Schema(Url()), "example.com")
    invalid(Schema(FqdnUrl()), "not-a-url")


def test_fqdn_url_good():
    assert Schema(FqdnUrl())("https://example.com") == "https://example.com"


# ---------------------------------------------------------------- boolean / truth

@pytest.mark.parametrize("value", ["true", "True", "1", 1, True])
def test_boolean_true_forms(value):
    assert Schema(Boolean())(value) is True


@pytest.mark.parametrize("value", ["false", "0", 0, False])
def test_boolean_false_forms(value):
    assert Schema(Boolean())(value) is False


def test_boolean_yes_is_true():
    assert Schema(Boolean())("yes") is True


def test_boolean_rejects_other_strings():
    invalid(Schema(Boolean()), "maybe")


def test_is_true_and_is_false_pass_values_through():
    assert Schema(IsTrue())(True) is True
    assert Schema(IsTrue())(1) == 1
    assert Schema(IsFalse())(False) is False
    assert Schema(IsFalse())(0) == 0
    invalid(Schema(IsTrue()), False)
    invalid(Schema(IsFalse()), True)


# ---------------------------------------------------------------- datetime / number

def test_datetime_default_iso_format():
    assert Schema(Datetime())("2024-01-02T03:04:05.123456Z") == "2024-01-02T03:04:05.123456Z"


def test_datetime_custom_format():
    assert Schema(Datetime(format="%Y/%m/%d"))("2024/01/02") == "2024/01/02"
    invalid(Schema(Datetime(format="%Y/%m/%d")), "2024-01-02")


def test_date_default_and_custom():
    assert Schema(Date())("2024-01-02") == "2024-01-02"
    invalid(Schema(Date()), "02/01/2024")


def test_number_precision_and_scale_are_total_digits_and_decimals():
    assert Schema(Number(precision=6, scale=2))("1234.01") == "1234.01"
    invalid(Schema(Number(precision=2)), "3.14")  # 3 digits, not 2
    invalid(Schema(Number(precision=6, scale=2)), "123.456")


def test_number_yield_decimal():
    from decimal import Decimal

    assert Schema(Number(precision=6, scale=2, yield_decimal=True))("1234.01") == Decimal("1234.01")


def test_number_rejects_non_numbers():
    invalid(Schema(Number()), "abc")
    invalid(Schema(Number()), None)


def test_number_without_constraints_passes_any_number():
    assert Schema(Number())(3.14159) == 3.14159
