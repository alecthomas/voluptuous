#!/usr/bin/env python3
"""
JSON Schema Export Examples for Voluptuous

This script demonstrates how to use the new JSON Schema export functionality
in voluptuous to convert voluptuous schemas to JSON Schema format.

The JSON Schema output can be used with:
- IDEs for YAML/JSON validation
- API documentation tools
- Schema validation libraries
- Code generation tools
"""

import json
from voluptuous import (
    Schema, Required, Optional, All, Any, Range, Length, In, Match, 
    Email, Url, Date, Datetime, Coerce, Clamp, ExactSequence, to_json_schema
)


def example_basic_types():
    """Demonstrate basic type conversion."""
    print("=== Basic Types ===")
    
    # Simple types
    schemas = {
        "String": Schema(str),
        "Integer": Schema(int),
        "Float": Schema(float),
        "Boolean": Schema(bool),
        "Literal": Schema("hello"),
        "None": Schema(None)
    }
    
    for name, schema in schemas.items():
        json_schema = schema.to_json_schema()
        print(f"{name}: {json.dumps(json_schema, indent=2)}")
        print()


def example_object_schemas():
    """Demonstrate object schema conversion."""
    print("=== Object Schemas ===")
    
    # User profile schema
    user_schema = Schema({
        Required('username'): All(str, Length(min=3, max=20)),
        Required('email'): Email(),
        Optional('age'): Range(min=13, max=120),
        Optional('bio', default=""): All(str, Length(max=500)),
        Optional('preferences'): {
            'theme': In(['light', 'dark', 'auto']),
            'notifications': bool,
            'language': str
        }
    })
    
    json_schema = user_schema.to_json_schema()
    print("User Profile Schema:")
    print(json.dumps(json_schema, indent=2))
    print()


def example_array_schemas():
    """Demonstrate array schema conversion."""
    print("=== Array Schemas ===")
    
    # Simple array
    simple_array = Schema([str])
    print("Simple String Array:")
    print(json.dumps(simple_array.to_json_schema(), indent=2))
    print()
    
    # Mixed array with exact sequence
    exact_sequence = Schema(ExactSequence([str, int, bool]))
    print("Exact Sequence [str, int, bool]:")
    print(json.dumps(exact_sequence.to_json_schema(), indent=2))
    print()
    
    # Set (unique items)
    unique_strings = Schema({str})
    print("Set of Strings (unique items):")
    print(json.dumps(unique_strings.to_json_schema(), indent=2))
    print()


def example_validators():
    """Demonstrate validator conversion."""
    print("=== Validators ===")
    
    validators = {
        "Range": Schema(Range(min=1, max=100)),
        "Length": Schema(All(str, Length(min=2, max=50))),
        "Email": Schema(Email()),
        "URL": Schema(Url()),
        "Date": Schema(Date()),
        "DateTime": Schema(Datetime()),
        "Pattern": Schema(Match(r'^[A-Z][a-z]+$')),
        "Enum": Schema(In(['red', 'green', 'blue'])),
        "Coerce": Schema(Coerce(int))
    }
    
    for name, schema in validators.items():
        json_schema = schema.to_json_schema()
        print(f"{name}:")
        print(json.dumps(json_schema, indent=2))
        print()


def example_composite_validators():
    """Demonstrate composite validator conversion."""
    print("=== Composite Validators ===")
    
    # All validator (must pass all conditions)
    all_validator = Schema(All(str, Length(min=1), Match(r'^[a-zA-Z]+$')))
    print("All(str, Length(min=1), Match('^[a-zA-Z]+$')):")
    print(json.dumps(all_validator.to_json_schema(), indent=2))
    print()
    
    # Any validator (must pass at least one condition)
    any_validator = Schema(Any(str, int, bool))
    print("Any(str, int, bool):")
    print(json.dumps(any_validator.to_json_schema(), indent=2))
    print()


def example_complex_schema():
    """Demonstrate a complex, real-world schema."""
    print("=== Complex Real-World Schema ===")
    
    # API configuration schema
    api_config_schema = Schema({
        Required('api'): {
            Required('name'): All(str, Length(min=1, max=100)),
            Required('version'): Match(r'^\d+\.\d+\.\d+$'),
            Required('endpoints'): [{
                Required('path'): All(str, Match(r'^/[a-zA-Z0-9/_-]*$')),
                Required('method'): In(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
                Optional('auth_required', default=True): bool,
                Optional('rate_limit'): Range(min=1, max=10000),
                Optional('description'): All(str, Length(max=500))
            }],
            Optional('database'): {
                Required('host'): str,
                Required('port'): Range(min=1, max=65535),
                Required('name'): All(str, Length(min=1, max=64)),
                Optional('ssl', default=True): bool,
                Optional('timeout', default=30): Range(min=1, max=300)
            }
        },
        Optional('logging'): {
            'level': In(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
            'format': str,
            'file': str
        },
        Optional('features'): {
            str: bool  # Feature flags
        }
    })
    
    json_schema = api_config_schema.to_json_schema()
    print("API Configuration Schema:")
    print(json.dumps(json_schema, indent=2))
    print()


def example_usage_with_data():
    """Show how the exported schema can validate actual data."""
    print("=== Usage Example ===")
    
    # Define a schema
    person_schema = Schema({
        Required('name'): All(str, Length(min=1, max=100)),
        Required('email'): Email(),
        Optional('age'): Range(min=0, max=150),
        Optional('tags'): [str]
    })
    
    # Export to JSON Schema
    json_schema = person_schema.to_json_schema()
    
    # Sample data that would be valid
    sample_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "tags": ["developer", "python"]
    }
    
    print("Voluptuous Schema:")
    print(f"Schema: {person_schema}")
    print()
    
    print("Exported JSON Schema:")
    print(json.dumps(json_schema, indent=2))
    print()
    
    print("Sample Valid Data:")
    print(json.dumps(sample_data, indent=2))
    print()
    
    # Validate with voluptuous
    try:
        validated = person_schema(sample_data)
        print("✓ Data is valid according to voluptuous schema")
        print(f"Validated data: {validated}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")


def main():
    """Run all examples."""
    print("Voluptuous JSON Schema Export Examples")
    print("=" * 50)
    print()
    
    example_basic_types()
    example_object_schemas()
    example_array_schemas()
    example_validators()
    example_composite_validators()
    example_complex_schema()
    example_usage_with_data()
    
    print("=" * 50)
    print("Examples completed!")
    print()
    print("You can now use these JSON Schemas with:")
    print("- JSON Schema validators")
    print("- IDE validation for YAML/JSON files")
    print("- API documentation tools")
    print("- Code generation tools")


if __name__ == "__main__":
    main()
