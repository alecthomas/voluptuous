"""Dataclasses support for voluptuous schemas.

This module provides functionality to automatically create voluptuous schemas
from Python dataclasses, with support for additional validation constraints.
"""

import dataclasses
import types
import typing
from copy import copy
from dataclasses import MISSING
from typing import Any, Dict, Optional, Type

from voluptuous import error as er
from voluptuous._i18n import gettext
from voluptuous.schema_builder import UNDEFINED
from voluptuous.schema_builder import Optional as OptionalMarker
from voluptuous.schema_builder import Required as RequiredMarker
from voluptuous.schema_builder import Schema
from voluptuous.validators import All
from voluptuous.validators import Any as AnyValidator


def is_dataclass(obj: Any) -> bool:
    """Check if an object is a dataclass.

    Args:
        obj: Object to check

    Returns:
        True if obj is a dataclass, False otherwise
    """
    return dataclasses.is_dataclass(obj)


def _field_annotations(dataclass_type):
    if not isinstance(dataclass_type, type) or not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass type")
    try:
        return typing.get_type_hints(
            dataclass_type,
            localns={dataclass_type.__name__: dataclass_type},
            include_extras=True,
        )
    except (NameError, TypeError) as exc:
        raise er.SchemaError(
            f"Cannot resolve annotations for {dataclass_type.__name__}: {exc}"
        ) from exc


def _annotation_schema(annotation, nested):
    """Translate supported annotations without silently dropping type arguments."""
    if annotation is Any:
        return object
    origin, args = typing.get_origin(annotation), typing.get_args(annotation)
    if origin is typing.Annotated:
        return _annotation_schema(args[0], nested)
    if origin in (typing.Union, types.UnionType):
        return AnyValidator(*(_annotation_schema(arg, nested) for arg in args))
    if origin is typing.Literal:

        def validate_literal(value):
            if any(type(value) is type(arg) and value == arg for arg in args):
                return value
            raise er.Invalid(gettext('value is not an allowed literal'))

        return validate_literal
    if isinstance(annotation, dataclasses.InitVar):
        return _annotation_schema(annotation.type, nested)
    if isinstance(annotation, type) and is_dataclass(annotation):
        return nested(annotation)
    if origin in (list, dict, set, frozenset, tuple):
        if not args and annotation not in (typing.Tuple[()], tuple[()]):
            return origin
        if origin is list:
            return [_annotation_schema(args[0], nested)]
        if origin is dict:
            return {
                _annotation_schema(args[0], nested): _annotation_schema(args[1], nested)
            }
        if origin in (set, frozenset):
            return origin([_annotation_schema(args[0], nested)])
        variadic = len(args) == 2 and args[1] is Ellipsis
        schemas = [
            Schema(_annotation_schema(arg, nested))
            for arg in (args[:1] if variadic else args)
        ]

        def validate_tuple(value):
            if not isinstance(value, tuple):
                raise er.TypeInvalid(gettext('expected tuple'))
            if not variadic and len(value) != len(schemas):
                raise er.LengthInvalid(gettext('invalid tuple length'))
            result = []
            for index, item in enumerate(value):
                try:
                    result.append(schemas[0 if variadic else index](item))
                except er.Invalid as exc:
                    exc.prepend([index])
                    raise
            return tuple(result)

        return validate_tuple
    if (
        origin is not None
        or not isinstance(annotation, type)
        or typing.is_typeddict(annotation)
    ):
        raise er.SchemaError(f"Unsupported dataclass annotation: {annotation!r}")
    return annotation


def get_dataclass_fields(dataclass_type: Type) -> Dict[str, Any]:
    """Extract field information from a dataclass.

    Args:
        dataclass_type: The dataclass type to extract fields from

    Returns:
        Dictionary mapping constructor field names to their resolved annotations

    Raises:
        ValueError: If the type is not a dataclass
    """
    annotations = _field_annotations(dataclass_type)
    stored = {field.name for field in dataclasses.fields(dataclass_type)}
    fields: Dict[str, Any] = {}
    for field_name, field_info in dataclass_type.__dataclass_fields__.items():
        annotation = annotations[field_name]
        if field_info.init and (
            field_name in stored or isinstance(annotation, dataclasses.InitVar)
        ):
            fields[field_name] = annotation
    return fields


def get_dataclass_field_defaults(dataclass_type: Type) -> Dict[str, Any]:
    """Extract default values from dataclass fields.

    Args:
        dataclass_type: The dataclass type to extract defaults from

    Returns:
        Dictionary mapping field names to their default values
    """
    if not is_dataclass(dataclass_type):
        return {}

    defaults = {}
    for field_name in get_dataclass_fields(dataclass_type):
        field_info = dataclass_type.__dataclass_fields__[field_name]
        if field_info.default is not MISSING:
            defaults[field_name] = field_info.default
        elif field_info.default_factory is not MISSING:
            defaults[field_name] = field_info.default_factory

    return defaults


def merge_constraints(base_constraint: Any, additional_constraint: Any) -> Any:
    """Merge two validation constraints using All validator.

    Args:
        base_constraint: The base constraint (usually a type)
        additional_constraint: Additional constraint to apply

    Returns:
        Combined constraint using All validator
    """
    return All(base_constraint, additional_constraint)


def merge_schema_constraints(
    base_schema: Dict[str, Any], additional_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge additional validation constraints into a base schema.

    Args:
        base_schema: Base schema dictionary (from dataclass fields)
        additional_schema: Additional constraints to merge

    Returns:
        Merged schema dictionary
    """
    result = {}

    # Start with all base schema fields
    for key, value in base_schema.items():
        if key in additional_schema:
            # Merge constraints for fields that have additional validation
            result[key] = merge_constraints(value, additional_schema[key])
        else:
            # Keep base constraint as-is
            result[key] = value

    # Add any additional fields that weren't in the base schema
    for key, value in additional_schema.items():
        if key not in base_schema:
            result[key] = value

    return result


def create_dataclass_schema(
    dataclass_type: Type,
    additional_constraints: Optional[Dict[str, Any]] = None,
    required: bool = False,
    extra: Any = UNDEFINED,
) -> Schema:
    """Create a voluptuous Schema from a dataclass.

    Args:
        dataclass_type: The dataclass type to create a schema for
        additional_constraints: Optional additional validation constraints
        required: Whether all fields should be required by default
        extra: How to handle extra fields (ALLOW_EXTRA, PREVENT_EXTRA, etc.)

    Returns:
        A voluptuous Schema that validates the dataclass

    Raises:
        ValueError: If dataclass_type is not a dataclass or dataclasses unavailable

    Example:
        Create a schema from a dataclass with additional constraints:

        @dataclass
        class Person:
            name: str
            age: int = 0

        schema = create_dataclass_schema(
            Person,
            {'age': Range(min=0, max=150)}
        )
        result = schema({'name': 'John', 'age': 30})
    """
    schemas = {}

    def nested(cls):
        # Delay compilation to permit self-referential dataclass annotations.
        def validate(value):
            if cls not in schemas:
                schemas[cls] = build(cls, {})
            return schemas[cls](value)

        return validate

    def build(cls, constraints):
        annotations = _field_annotations(cls)
        constructor = get_dataclass_fields(cls)
        stored = {field.name: field for field in dataclasses.fields(cls)}
        compiled_fields = {
            name: _annotation_schema(annotations[name], nested)
            for name in dict.fromkeys([*constructor, *stored])
        }
        constructor_schema = merge_schema_constraints(
            {name: compiled_fields[name] for name in constructor}, constraints
        )
        mapping = {}
        for name, constraint in constructor_schema.items():
            field_info = cls.__dataclass_fields__.get(name)
            if name not in constructor:
                marker = name
            elif field_info.default is not MISSING:
                # A callable default is a value; only default_factory is invoked.
                marker = OptionalMarker(
                    name, default=lambda value=field_info.default: value
                )
            elif field_info.default_factory is not MISSING:
                marker = OptionalMarker(name, default=field_info.default_factory)
            else:
                marker = RequiredMarker(name)
            mapping[marker] = constraint
        options = {'required': required}
        if extra is not UNDEFINED:
            options['extra'] = extra
        dict_schema = Schema(mapping, **options)
        instance_schema = Schema(
            {
                RequiredMarker(name): (
                    All(compiled_fields[name], constraints[name])
                    if name in constraints
                    else compiled_fields[name]
                )
                for name in stored
            }
        )

        def validate(data):
            if isinstance(data, cls):
                values = instance_schema(
                    {
                        name: getattr(data, name)
                        for name in stored
                        if hasattr(data, name)
                    }
                )
                result = copy(data)
                for name, value in values.items():
                    object.__setattr__(result, name, value)
                return result
            if is_dataclass(data):
                raise er.ObjectInvalid(gettext('expected a {0!r}').format(cls))
            values = dict_schema(data)
            return cls(
                **{name: value for name, value in values.items() if name in constructor}
            )

        return Schema(validate)

    result = build(dataclass_type, additional_constraints or {})
    schemas[dataclass_type] = result
    return result


class DataclassSchema(Schema):
    """A Schema subclass that automatically handles dataclasses.

    This class provides a convenient way to create schemas from dataclasses
    with additional validation constraints.

    Example:
        Create a schema from a dataclass with additional constraints:

        @dataclass
        class Person:
            name: str
            age: int = 0

        schema = DataclassSchema(Person, {'age': Range(min=0, max=150)})
        result = schema({'name': 'John', 'age': 30})
    """

    def __init__(
        self,
        dataclass_type: Type,
        additional_constraints: Optional[Dict[str, Any]] = None,
        required: bool = False,
        extra: Any = UNDEFINED,
    ):
        """Initialize a DataclassSchema.

        Args:
            dataclass_type: The dataclass type to create a schema for
            additional_constraints: Optional additional validation constraints
            required: Whether all fields should be required by default
            extra: How to handle extra fields
        """
        if not is_dataclass(dataclass_type):
            raise ValueError(f"{dataclass_type} is not a dataclass")

        self.dataclass_type = dataclass_type
        self.additional_constraints = additional_constraints or {}

        # Create the schema using the helper function
        schema = create_dataclass_schema(
            dataclass_type, additional_constraints, required, extra
        )

        # Initialize parent Schema with the created schema
        super().__init__(
            schema.schema,
            required=required,
            extra=extra if extra is not UNDEFINED else schema.extra,
        )
