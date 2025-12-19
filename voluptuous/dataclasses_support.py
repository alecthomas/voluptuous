"""Dataclasses support for voluptuous schemas.

This module provides functionality to automatically create voluptuous schemas
from Python dataclasses, with support for additional validation constraints.

Requires Python 3.7+ for dataclasses support.
"""

import sys
from typing import Any, Dict, Optional, Type

from voluptuous.schema_builder import UNDEFINED
from voluptuous.schema_builder import Optional as OptionalMarker
from voluptuous.schema_builder import Required as RequiredMarker
from voluptuous.schema_builder import Schema
from voluptuous.validators import All

# Check if dataclasses is available (Python 3.7+)
if sys.version_info >= (3, 7):
    try:
        import dataclasses
        from dataclasses import MISSING, Field

        DATACLASSES_AVAILABLE = True
    except ImportError:
        DATACLASSES_AVAILABLE = False
        dataclasses = None  # type: ignore
        Field = None  # type: ignore
        MISSING = None  # type: ignore
else:
    DATACLASSES_AVAILABLE = False
    dataclasses = None  # type: ignore
    Field = None  # type: ignore
    MISSING = None  # type: ignore


def is_dataclass(obj: Any) -> bool:
    """Check if an object is a dataclass.

    Args:
        obj: Object to check

    Returns:
        True if obj is a dataclass, False otherwise
    """
    if not DATACLASSES_AVAILABLE:
        return False
    return dataclasses.is_dataclass(obj)


def get_dataclass_fields(dataclass_type: Type) -> Dict[str, Any]:
    """Extract field information from a dataclass.

    Args:
        dataclass_type: The dataclass type to extract fields from

    Returns:
        Dictionary mapping field names to their basic types

    Raises:
        ValueError: If the type is not a dataclass
    """
    if not DATACLASSES_AVAILABLE:
        raise ValueError("Dataclasses are not available (requires Python 3.7+)")

    if not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass")

    fields: Dict[str, Any] = {}
    for field_name, field_info in dataclass_type.__dataclass_fields__.items():
        field_type = field_info.type

        # Convert typing annotations to basic types for voluptuous
        # For complex types like List[str], Optional[str], etc., we'll use the base type
        # and let additional constraints handle the specifics
        if hasattr(field_type, '__origin__'):
            # Handle generic types like List[str], Optional[str], etc.
            origin = field_type.__origin__
            if origin is list:
                fields[field_name] = list
            elif origin is dict:
                fields[field_name] = dict
            elif origin is set:
                fields[field_name] = set
            elif origin is tuple:
                fields[field_name] = tuple
            elif (
                hasattr(field_type, '__args__')
                and len(field_type.__args__) == 2
                and type(None) in field_type.__args__
            ):
                # Optional[T] is Union[T, None]
                non_none_type = next(
                    arg for arg in field_type.__args__ if arg is not type(None)
                )
                fields[field_name] = non_none_type
            else:
                # For other generic types, use the origin
                fields[field_name] = origin
        else:
            # Simple type, use as-is
            fields[field_name] = field_type

    return fields


def get_dataclass_field_defaults(dataclass_type: Type) -> Dict[str, Any]:
    """Extract default values from dataclass fields.

    Args:
        dataclass_type: The dataclass type to extract defaults from

    Returns:
        Dictionary mapping field names to their default values
    """
    if not DATACLASSES_AVAILABLE:
        return {}

    if not is_dataclass(dataclass_type):
        return {}

    defaults = {}
    for field_name, field_info in dataclass_type.__dataclass_fields__.items():
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
    if not DATACLASSES_AVAILABLE:
        raise ValueError("Dataclasses are not available (requires Python 3.7+)")

    if not is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass")

    # Extract field types from dataclass
    base_schema = get_dataclass_fields(dataclass_type)

    # Merge with additional constraints if provided
    if additional_constraints:
        schema_dict = merge_schema_constraints(base_schema, additional_constraints)
    else:
        schema_dict = base_schema.copy()

    # Convert to proper voluptuous schema with markers
    voluptuous_schema: Dict[Any, Any] = {}

    for field_name, constraint in schema_dict.items():
        field_info = dataclass_type.__dataclass_fields__.get(field_name)

        if field_info and field_info.default is not MISSING:
            # Field has a default value - make it Optional
            voluptuous_schema[
                OptionalMarker(field_name, default=field_info.default)
            ] = constraint
        elif field_info and field_info.default_factory is not MISSING:
            # Field has a default factory - make it Optional
            voluptuous_schema[
                OptionalMarker(field_name, default=field_info.default_factory)
            ] = constraint
        elif field_name in base_schema:
            # Field is from dataclass but has no default - make it Required
            voluptuous_schema[RequiredMarker(field_name)] = constraint
        else:
            # Additional field not in dataclass - use as-is
            voluptuous_schema[field_name] = constraint

    # Create a custom validator that validates dict and creates dataclass instance
    def dataclass_validator(data):
        # First validate the dictionary structure
        if extra is not UNDEFINED:
            dict_schema = Schema(voluptuous_schema, required=required, extra=extra)
        else:
            dict_schema = Schema(voluptuous_schema, required=required)
        validated_data = dict_schema(data)

        # Extract the actual values (removing marker wrappers)
        clean_data = {}
        for key, value in validated_data.items():
            clean_data[key] = value

        # Create and return dataclass instance
        return dataclass_type(**clean_data)

    # Return a schema with the custom validator
    return Schema(dataclass_validator)


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
        if not DATACLASSES_AVAILABLE:
            raise ValueError("Dataclasses are not available (requires Python 3.7+)")

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
