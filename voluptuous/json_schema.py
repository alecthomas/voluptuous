"""JSON Schema export functionality for voluptuous schemas.

This module provides functionality to convert voluptuous schemas to JSON Schema format,
enabling integration with modern IDEs and validation tools that support JSON Schema.
"""

import inspect
import typing
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, Union

from voluptuous import validators as v
from voluptuous.schema_builder import (
    Extra,
    Marker,
)
from voluptuous.schema_builder import Optional as OptionalMarker
from voluptuous.schema_builder import (
    Remove,
)
from voluptuous.schema_builder import Required as RequiredMarker
from voluptuous.schema_builder import (
    Schema,
    primitive_types,
)


class JsonSchemaConverter:
    """Converts voluptuous schemas to JSON Schema format.

    This converter traverses voluptuous schema structures and generates
    equivalent JSON Schema representations that preserve validation semantics
    where possible.
    """

    def __init__(self, schema: Schema):
        """Initialize converter with a voluptuous schema.

        Args:
            schema: The voluptuous Schema instance to convert
        """
        self.schema = schema
        self.definitions: Dict[str, Any] = {}
        self._ref_counter = 0

    def convert(self) -> Dict[str, Any]:
        """Convert the voluptuous schema to JSON Schema format.

        Returns:
            A dictionary representing the JSON Schema
        """
        json_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
        }

        # Convert the main schema
        converted = self._convert_schema_element(self.schema.schema)

        # Merge the converted schema
        if isinstance(converted, dict):
            json_schema.update(converted)
        else:
            # If it's not a dict, wrap it appropriately
            json_schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                **self._wrap_non_object_schema(converted),
            }

        # Add definitions if any were created
        if self.definitions:
            json_schema["$defs"] = self.definitions

        return json_schema

    def _convert_schema_element(self, element: Any) -> Any:
        """Convert a single schema element to JSON Schema format.

        Args:
            element: The schema element to convert

        Returns:
            JSON Schema representation of the element
        """
        # Handle None
        if element is None:
            return {"type": "null"}

        # Handle Extra marker
        if element is Extra:
            return True  # Allow additional properties

        # Handle Marker classes (Required, Optional, Remove)
        if isinstance(element, Marker):
            return self._convert_marker(element)

        # Handle primitive types
        if element in primitive_types:
            return self._convert_primitive_type(element)

        # Handle Schema instances
        if isinstance(element, Schema):
            return self._convert_schema_element(element.schema)

        # Handle mappings (dictionaries)
        if isinstance(element, Mapping):
            return self._convert_mapping(element)

        # Handle sequences (lists, tuples)
        if isinstance(element, (list, tuple)):
            return self._convert_sequence(element)

        # Handle sets
        if isinstance(element, (set, frozenset)):
            return self._convert_set(element)

        # Handle validator classes
        if hasattr(element, '__class__') and hasattr(element.__class__, '__name__'):
            converter_method = getattr(
                self, f'_convert_{element.__class__.__name__.lower()}', None
            )
            if converter_method:
                return converter_method(element)

        # Handle callable validators (including decorated functions like Email, Url)
        if callable(element):
            # Check if it's a known validator function by name
            func_name = getattr(element, '__name__', '').lower()
            if func_name:
                converter_method = getattr(self, f'_convert_{func_name}', None)
                if converter_method:
                    return converter_method(element)

            return self._convert_callable(element)

        # Handle literal values
        return self._convert_literal(element)

    def _convert_primitive_type(self, type_class: type) -> Dict[str, str]:
        """Convert Python primitive types to JSON Schema types."""
        type_mapping = {
            bool: "boolean",
            int: "integer",
            float: "number",
            str: "string",
            bytes: "string",  # JSON Schema doesn't have bytes, use string
            complex: "string",  # Complex numbers as strings
        }
        return {"type": type_mapping.get(type_class, "string")}

    def _convert_mapping(self, mapping: Mapping) -> Dict[str, Any]:
        """Convert a mapping (dictionary) schema to JSON Schema object."""
        json_schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

        required_keys = []

        for key, value in mapping.items():
            if key is Extra:
                json_schema["additionalProperties"] = True
                continue

            # Handle marker keys
            if isinstance(key, RequiredMarker):
                prop_name = str(key.schema)
                required_keys.append(prop_name)
                json_schema["properties"][prop_name] = self._convert_schema_element(
                    value
                )
            elif isinstance(key, OptionalMarker):
                prop_name = str(key.schema)
                json_schema["properties"][prop_name] = self._convert_schema_element(
                    value
                )
                # Add default if specified
                if hasattr(key, 'default') and key.default is not None:
                    # Handle default_factory functions
                    if callable(key.default):
                        try:
                            default_value = key.default()
                            # Only add if the default value is JSON serializable
                            if self._is_json_serializable(default_value):
                                json_schema["properties"][prop_name][
                                    "default"
                                ] = default_value
                        except:
                            # If default factory fails, skip adding default
                            pass
                    else:
                        # Only add if the default value is JSON serializable
                        if self._is_json_serializable(key.default):
                            json_schema["properties"][prop_name][
                                "default"
                            ] = key.default
            elif isinstance(key, Remove):
                # Remove markers are ignored in JSON Schema
                continue
            else:
                # Regular key
                prop_name = str(key)
                json_schema["properties"][prop_name] = self._convert_schema_element(
                    value
                )
                # In voluptuous, regular keys are required by default if schema.required is True
                if getattr(self.schema, 'required', False):
                    required_keys.append(prop_name)

        if required_keys:
            json_schema["required"] = required_keys

        return json_schema

    def _convert_sequence(self, sequence: Sequence) -> Dict[str, Any]:
        """Convert a sequence (list/tuple) schema to JSON Schema array."""
        if not sequence:
            return {"type": "array", "maxItems": 0}

        # Convert all items to schemas first
        items_schemas = [self._convert_schema_element(item) for item in sequence]

        # Check if all converted schemas are identical
        if len(items_schemas) == 1 or all(
            schema == items_schemas[0] for schema in items_schemas
        ):
            # All items have the same schema - use single items schema
            return {"type": "array", "items": items_schemas[0]}

        # Multiple different schemas - use prefixItems for ordered validation
        return {
            "type": "array",
            "prefixItems": items_schemas,
            "items": False,  # No additional items allowed
        }

    def _convert_set(self, set_schema: Union[set, frozenset]) -> Dict[str, Any]:
        """Convert a set schema to JSON Schema array with unique items."""
        if not set_schema:
            return {"type": "array", "uniqueItems": True, "maxItems": 0}

        # Convert the single item type in the set
        item_schema = self._convert_schema_element(next(iter(set_schema)))
        return {"type": "array", "items": item_schema, "uniqueItems": True}

    def _convert_marker(self, marker: Marker) -> Any:
        """Convert a Marker instance to its underlying schema."""
        return self._convert_schema_element(marker.schema)

    def _convert_callable(self, func: callable) -> Dict[str, Any]:
        """Convert a callable validator to JSON Schema."""
        # For generic callables, we can't determine much about the expected type
        # This is a limitation of the conversion process
        return {
            "description": f"Custom validator: {getattr(func, '__name__', 'anonymous')}"
        }

    def _convert_literal(self, value: Any) -> Dict[str, Any]:
        """Convert a literal value to JSON Schema const."""
        return {"const": value}

    def _wrap_non_object_schema(self, schema: Any) -> Dict[str, Any]:
        """Wrap non-object schemas appropriately."""
        if isinstance(schema, dict) and "type" in schema:
            return schema
        return {"type": "string", "description": "Complex schema"}

    def _is_json_serializable(self, value: Any) -> bool:
        """Check if a value is JSON serializable."""
        try:
            import json

            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False

    # Validator-specific conversion methods

    def _convert_range(self, range_validator: v.Range) -> Dict[str, Any]:
        """Convert Range validator to JSON Schema numeric constraints."""
        schema = {"type": "number"}

        if hasattr(range_validator, 'min') and range_validator.min is not None:
            if getattr(range_validator, 'min_included', True):
                schema["minimum"] = range_validator.min
            else:
                schema["exclusiveMinimum"] = range_validator.min

        if hasattr(range_validator, 'max') and range_validator.max is not None:
            if getattr(range_validator, 'max_included', True):
                schema["maximum"] = range_validator.max
            else:
                schema["exclusiveMaximum"] = range_validator.max

        return schema

    def _convert_length(self, length_validator: v.Length) -> Dict[str, Any]:
        """Convert Length validator to JSON Schema string/array length constraints."""
        schema = {}

        if hasattr(length_validator, 'min') and length_validator.min is not None:
            schema["minLength"] = length_validator.min

        if hasattr(length_validator, 'max') and length_validator.max is not None:
            schema["maxLength"] = length_validator.max

        return schema

    def _convert_all(self, all_validator: v.All) -> Dict[str, Any]:
        """Convert All validator to JSON Schema allOf constraint."""
        if not hasattr(all_validator, 'validators'):
            return {}

        schemas = []
        for validator in all_validator.validators:
            converted = self._convert_schema_element(validator)
            if converted:
                schemas.append(converted)

        if len(schemas) == 1:
            return schemas[0]
        elif len(schemas) > 1:
            return {"allOf": schemas}
        else:
            return {}

    def _convert_any(self, any_validator: v.Any) -> Dict[str, Any]:
        """Convert Any validator to JSON Schema anyOf constraint."""
        if not hasattr(any_validator, 'validators'):
            return {}

        schemas = []
        for validator in any_validator.validators:
            converted = self._convert_schema_element(validator)
            if converted:
                schemas.append(converted)

        if len(schemas) == 1:
            return schemas[0]
        elif len(schemas) > 1:
            return {"anyOf": schemas}
        else:
            return {}

    def _convert_in(self, in_validator: v.In) -> Dict[str, Any]:
        """Convert In validator to JSON Schema enum constraint."""
        if hasattr(in_validator, 'container'):
            return {"enum": list(in_validator.container)}
        return {}

    def _convert_match(self, match_validator: v.Match) -> Dict[str, Any]:
        """Convert Match validator to JSON Schema pattern constraint."""
        if hasattr(match_validator, 'pattern'):
            pattern = match_validator.pattern
            if hasattr(pattern, 'pattern'):  # compiled regex
                pattern = pattern.pattern
            return {"type": "string", "pattern": pattern}
        return {"type": "string"}

    def _convert_email(self, email_validator: v.Email) -> Dict[str, Any]:
        """Convert Email validator to JSON Schema email format."""
        return {"type": "string", "format": "email"}

    def _convert_url(self, url_validator: v.Url) -> Dict[str, Any]:
        """Convert Url validator to JSON Schema uri format."""
        return {"type": "string", "format": "uri"}

    def _convert_date(self, date_validator: v.Date) -> Dict[str, Any]:
        """Convert Date validator to JSON Schema date format."""
        return {"type": "string", "format": "date"}

    def _convert_datetime(self, datetime_validator: v.Datetime) -> Dict[str, Any]:
        """Convert Datetime validator to JSON Schema date-time format."""
        return {"type": "string", "format": "date-time"}

    def _convert_coerce(self, coerce_validator: v.Coerce) -> Dict[str, Any]:
        """Convert Coerce validator based on target type."""
        if hasattr(coerce_validator, 'type'):
            return self._convert_primitive_type(coerce_validator.type)
        return {}

    def _convert_clamp(self, clamp_validator: v.Clamp) -> Dict[str, Any]:
        """Convert Clamp validator to Range-like constraints."""
        schema = {"type": "number"}

        if hasattr(clamp_validator, 'min') and clamp_validator.min is not None:
            schema["minimum"] = clamp_validator.min

        if hasattr(clamp_validator, 'max') and clamp_validator.max is not None:
            schema["maximum"] = clamp_validator.max

        return schema

    def _convert_exactsequence(
        self, exact_validator: v.ExactSequence
    ) -> Dict[str, Any]:
        """Convert ExactSequence validator to JSON Schema with exact items."""
        if hasattr(exact_validator, 'validators'):
            items_schemas = [
                self._convert_schema_element(validator)
                for validator in exact_validator.validators
            ]
            return {
                "type": "array",
                "prefixItems": items_schemas,
                "items": False,  # No additional items
                "minItems": len(items_schemas),
                "maxItems": len(items_schemas),
            }
        return {"type": "array"}


def to_json_schema(schema: Union[Schema, Any]) -> Dict[str, Any]:
    """Convert a voluptuous schema to JSON Schema format.

    This is a convenience function that creates a JsonSchemaConverter
    and performs the conversion.

    Args:
        schema: A voluptuous Schema instance or schema definition

    Returns:
        A dictionary representing the JSON Schema

    Example:
        >>> from voluptuous import Schema, Required, Range
        >>> schema = Schema({Required('name'): str, 'age': Range(min=0, max=120)})
        >>> json_schema = to_json_schema(schema)
        >>> print(json_schema['properties']['name'])
        {'type': 'string'}
    """
    if not isinstance(schema, Schema):
        schema = Schema(schema)

    converter = JsonSchemaConverter(schema)
    return converter.convert()
