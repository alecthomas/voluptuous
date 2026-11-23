"""Regressions for instance validation and resolved dataclass annotations."""

from dataclasses import InitVar, dataclass, field
from typing import Any, ClassVar, Literal, Optional, Sequence

import pytest

from voluptuous import (
    ALLOW_EXTRA,
    REMOVE_EXTRA,
    DataclassSchema,
    MultipleInvalid,
    Range,
    Schema,
    SchemaError,
    create_dataclass_schema,
)


@pytest.mark.parametrize('factory', [DataclassSchema, create_dataclass_schema])
def test_issue_inventory_instance(factory):
    @dataclass
    class InventoryItem:
        name: str
        unit_price: float
        quantity_on_hand: int = 0

    validate = factory(InventoryItem, {'unit_price': Range(min=5)})
    item = InventoryItem('nails', 6.5, 4)
    result = validate(item)
    assert result == item and result is not item
    with pytest.raises(MultipleInvalid) as exc:
        validate(InventoryItem('nails', 3.33, 4))
    assert exc.value.path == ['unit_price']
    assert validate({'name': 'nails', 'unit_price': 6.5}) == InventoryItem('nails', 6.5)


@pytest.mark.parametrize('frozen,slots', [(False, False), (True, False), (True, True)])
def test_instance_copy_preserves_non_init_fields_without_rerunning_constructor(
    frozen, slots
):
    calls = []

    @dataclass(frozen=frozen, slots=slots)  # type: ignore[literal-required]
    class Record:
        value: str
        token: InitVar[str]
        computed: str = field(init=False)
        kind: ClassVar[str] = 'record'

        def __post_init__(self, token):
            calls.append(token)
            object.__setattr__(self, 'computed', token)

    original = Record(' hello ', 'private')
    validate = DataclassSchema(Record, {'value': str.strip, 'computed': str.upper})
    result = validate(original)
    assert result.value == 'hello'
    assert result.computed == 'PRIVATE'
    assert original.value == ' hello ' and original.computed == 'private'
    assert calls == ['private']


def test_constructor_initvar_classvar_and_factory():
    calls = []

    @dataclass
    class Record:
        value: int
        multiplier: InitVar[int]
        items: list[int] = field(default_factory=list)
        computed: int = field(init=False)
        kind: ClassVar[str] = 'record'

        def __post_init__(self, multiplier):
            calls.append(multiplier)
            self.computed = self.value * multiplier

    validate = DataclassSchema(Record)
    first = validate({'value': 3, 'multiplier': 2})
    second = validate({'value': 4, 'multiplier': 3})
    assert first.computed == 6 and second.computed == 12
    assert first.items is not second.items
    with pytest.raises(MultipleInvalid) as exc:
        validate({'value': 3, 'multiplier': 'bad'})
    assert exc.value.path == ['multiplier']
    assert calls == [2, 3]
    with pytest.raises(MultipleInvalid) as exc:
        validate({'value': 3, 'multiplier': 2, 'kind': 'different'})
    assert exc.value.path == ['kind']


def test_subclass_identity_and_unrelated_instance():
    @dataclass
    class Base:
        value: str

    @dataclass
    class Child(Base):
        extra: int = 7

    @dataclass
    class Unrelated:
        value: str

    validate = DataclassSchema(Base, {'value': str.upper})
    original = Child('hello')
    original.cache = 'retained'
    result = validate(original)
    assert type(result) is Child and result.extra == 7 and result.cache == 'retained'
    assert result.value == 'HELLO' and original.value == 'hello'
    with pytest.raises(MultipleInvalid):
        validate(Unrelated('hello'))


def test_optional_and_union_annotations():
    @dataclass
    class Record:
        value: Optional[int] = None
        other: str | int = 0
        anything: Any = None

    validate = DataclassSchema(Record)
    assert validate({}) == Record()
    assert validate(Record()) == Record()
    assert validate({'other': 'str', 'anything': [1]}) == Record(None, 'str', [1])
    with pytest.raises(MultipleInvalid) as exc:
        validate({'value': 'wrong'})
    assert exc.value.path == ['value']


def test_nested_dataclasses_and_collection_error_paths():
    @dataclass
    class Child:
        value: int

    @dataclass
    class Parent:
        children: list[Child]
        labels: dict[str, list[int]]
        flags: set[str]
        frozen: frozenset[int]

    validate = Schema({'record': DataclassSchema(Parent)})
    data = {
        'record': {
            'children': [{'value': 3}],
            'labels': {'a': [1]},
            'flags': {'ok'},
            'frozen': frozenset({2}),
        }
    }
    result = validate(data)['record']
    assert result == Parent([Child(3)], {'a': [1]}, {'ok'}, frozenset({2}))
    assert data['record']['children'] == [{'value': 3}]
    data['record']['children'][0]['value'] = 'wrong'
    with pytest.raises(MultipleInvalid) as exc:
        validate(data)
    assert exc.value.path == ['record', 'children', 0, 'value']


def test_future_annotations_and_recursive_dataclass():
    @dataclass
    class Node:
        value: 'int'
        children: 'list[Node]' = field(default_factory=list)

    validate = DataclassSchema(Node)
    assert validate({'value': 1, 'children': [{'value': 2}]}) == Node(1, [Node(2)])
    with pytest.raises(MultipleInvalid) as exc:
        validate({'value': 1, 'children': [{'value': 'wrong'}]})
    assert exc.value.path == ['children', 0, 'value']


def test_tuple_annotations_and_literal_types():
    @dataclass
    class Record:
        pair: tuple[str, int]
        many: tuple[int, ...]
        empty: tuple[()]
        enabled: Literal[True]

    validate = DataclassSchema(Record)
    data = {'pair': ('a', 2), 'many': (1, 2, 3), 'empty': (), 'enabled': True}
    assert validate(data) == Record(('a', 2), (1, 2, 3), (), True)
    for field_name, bad, error_path in [
        ('pair', ('a', 'bad'), ['pair', 1]),
        ('pair', ('a',), ['pair']),
        ('many', [1, 2], ['many']),
        ('many', (1, 'bad'), ['many', 1]),
        ('empty', (1,), ['empty']),
        ('enabled', 1, ['enabled']),
    ]:
        with pytest.raises(MultipleInvalid) as exc:
            validate({**data, field_name: bad})
        assert exc.value.path == error_path


@pytest.mark.parametrize('extra', [ALLOW_EXTRA, REMOVE_EXTRA])
def test_extra_keys_are_not_constructor_arguments(extra):
    @dataclass
    class Record:
        value: int

    assert DataclassSchema(Record, extra=extra)({'value': 1, 'extra': 2}) == Record(1)
    assert DataclassSchema(Record, {'comment': str})(
        {'value': 1, 'comment': 'ok'}
    ) == Record(1)


def test_callable_default_is_not_a_factory():
    def callback():
        raise AssertionError('a callable default must not be invoked')

    @dataclass
    class Record:
        handler: object = callback

    assert DataclassSchema(Record)({}).handler is callback


def test_invalid_schema_types_are_reported_at_construction():
    @dataclass
    class Unknown:
        value: 'NotDefinedAnywhere'  # noqa: F821 - intentionally unresolved

    @dataclass
    class Unsupported:
        value: Sequence[int]

    @dataclass
    class Record:
        value: int

    with pytest.raises(SchemaError, match='Cannot resolve annotations'):
        DataclassSchema(Unknown)
    with pytest.raises(SchemaError, match='Unsupported dataclass annotation'):
        DataclassSchema(Unsupported)
    with pytest.raises(ValueError, match='dataclass type'):
        DataclassSchema(Record(1))
