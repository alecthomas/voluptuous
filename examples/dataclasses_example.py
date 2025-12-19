#!/usr/bin/env python3
"""
Dataclasses Support Examples for Voluptuous

This script demonstrates how to use the new dataclasses support functionality
in voluptuous to automatically create schemas from Python dataclasses.

Requires Python 3.7+ for dataclasses support.
"""

import sys
from dataclasses import dataclass, field
from typing import List, Optional

# Check if we have dataclasses support
if sys.version_info < (3, 7):
    print("This example requires Python 3.7+ for dataclasses support")
    sys.exit(1)

from voluptuous import (
    All,
    Any,
    DataclassSchema,
    Email,
    In,
    Length,
    Match,
    Range,
    Schema,
    create_dataclass_schema,
    is_dataclass,
)


def example_basic_dataclass():
    """Demonstrate basic dataclass schema creation."""
    print("=== Basic Dataclass Schema ===")

    @dataclass
    class Person:
        name: str
        age: int
        active: bool = True

    # Create schema from dataclass
    schema = DataclassSchema(Person)

    # Test with valid data
    result = schema({'name': 'John Doe', 'age': 30, 'active': False})

    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    print(f"Name: {result.name}")
    print(f"Age: {result.age}")
    print(f"Active: {result.active}")
    print()

    # Test with defaults
    result2 = schema({'name': 'Jane Smith', 'age': 25})
    print(f"With defaults: {result2}")
    print(f"Active (default): {result2.active}")
    print()


def example_dataclass_with_constraints():
    """Demonstrate dataclass with additional validation constraints."""
    print("=== Dataclass with Validation Constraints ===")

    @dataclass
    class User:
        username: str
        email: str
        age: int = 18
        bio: str = ""

    # Create schema with additional constraints
    schema = DataclassSchema(
        User,
        {
            'username': All(str, Length(min=3, max=20), Match(r'^[a-zA-Z0-9_]+$')),
            'email': Email(),
            'age': Range(min=13, max=120),
            'bio': All(str, Length(max=500)),
        },
    )

    # Test valid data
    result = schema(
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'age': 25,
            'bio': 'Software developer with 5 years of experience.',
        }
    )

    print(f"Valid user: {result}")
    print()

    # Test validation errors
    try:
        schema({'username': 'jo', 'email': 'john@example.com', 'age': 25})  # Too short
    except Exception as e:
        print(f"Validation error (short username): {e}")

    try:
        schema(
            {
                'username': 'john_doe',
                'email': 'invalid-email',  # Invalid email
                'age': 25,
            }
        )
    except Exception as e:
        print(f"Validation error (invalid email): {e}")

    print()


def example_nested_dataclasses():
    """Demonstrate nested dataclass validation."""
    print("=== Nested Dataclass Validation ===")

    @dataclass
    class Address:
        street: str
        city: str
        zipcode: str
        country: str = "USA"

    @dataclass
    class Person:
        name: str
        age: int
        address: dict  # Will be validated as Address

    # Create schemas
    address_schema = DataclassSchema(
        Address, {'zipcode': Match(r'^\d{5}(-\d{4})?$')}  # US zipcode format
    )

    person_schema = DataclassSchema(
        Person,
        {
            'name': Length(min=1, max=100),
            'age': Range(min=0, max=150),
            'address': address_schema,
        },
    )

    # Test nested validation
    result = person_schema(
        {
            'name': 'Alice Johnson',
            'age': 28,
            'address': {
                'street': '123 Main St',
                'city': 'Anytown',
                'zipcode': '12345',
                'country': 'USA',
            },
        }
    )

    print(f"Person: {result}")
    print(f"Address type: {type(result.address)}")
    print(f"Street: {result.address.street}")
    print(f"City: {result.address.city}")
    print()


def example_dataclass_with_lists():
    """Demonstrate dataclass with list fields."""
    print("=== Dataclass with List Fields ===")

    @dataclass
    class Project:
        name: str
        description: str
        tags: List[str] = field(default_factory=list)
        team_members: List[str] = field(default_factory=list)

    schema = DataclassSchema(
        Project,
        {
            'name': All(str, Length(min=1, max=100)),
            'description': All(str, Length(min=10, max=1000)),
            'tags': [All(str, Length(min=1))],  # List of non-empty strings
            'team_members': [All(str, Length(min=1))],  # List of non-empty strings
        },
    )

    # Test with list data
    result = schema(
        {
            'name': 'Awesome Project',
            'description': 'This is a really awesome project that does amazing things.',
            'tags': ['python', 'web', 'api'],
            'team_members': ['Alice', 'Bob', 'Charlie'],
        }
    )

    print(f"Project: {result}")
    print(f"Tags: {result.tags}")
    print(f"Team: {result.team_members}")
    print()

    # Test with defaults
    result2 = schema(
        {
            'name': 'Simple Project',
            'description': 'A simple project with minimal requirements.',
        }
    )

    print(f"Project with defaults: {result2}")
    print(f"Default tags: {result2.tags}")
    print(f"Default team: {result2.team_members}")
    print()


def example_create_dataclass_schema_function():
    """Demonstrate the create_dataclass_schema function."""
    print("=== Using create_dataclass_schema Function ===")

    @dataclass
    class Product:
        name: str
        price: float
        category: str
        in_stock: bool = True
        description: Optional[str] = None

    # Use the standalone function
    schema = create_dataclass_schema(
        Product,
        {
            'name': All(str, Length(min=1, max=200)),
            'price': All(float, Range(min=0)),
            'category': In(['electronics', 'books', 'clothing', 'home', 'sports']),
            'description': Any(None, All(str, Length(min=10, max=1000))),
        },
    )

    # Test the schema
    result = schema(
        {
            'name': 'Wireless Headphones',
            'price': 99.99,
            'category': 'electronics',
            'in_stock': True,
            'description': 'High-quality wireless headphones with noise cancellation.',
        }
    )

    print(f"Product: {result}")
    print(f"Price: ${result.price}")
    print(f"In stock: {result.in_stock}")
    print()


def example_dataclass_detection():
    """Demonstrate dataclass detection functionality."""
    print("=== Dataclass Detection ===")

    @dataclass
    class DataclassExample:
        field1: str
        field2: int

    class RegularClass:
        def __init__(self, field1, field2):
            self.field1 = field1
            self.field2 = field2

    # Test detection
    print(f"DataclassExample is dataclass: {is_dataclass(DataclassExample)}")
    print(
        f"DataclassExample instance is dataclass: {is_dataclass(DataclassExample('test', 1))}"
    )
    print(f"RegularClass is dataclass: {is_dataclass(RegularClass)}")
    print(
        f"RegularClass instance is dataclass: {is_dataclass(RegularClass('test', 1))}"
    )
    print(f"str is dataclass: {is_dataclass(str)}")
    print(f"'hello' is dataclass: {is_dataclass('hello')}")
    print()


def example_complex_validation():
    """Demonstrate complex validation scenarios."""
    print("=== Complex Validation Scenarios ===")

    @dataclass
    class APIConfig:
        name: str
        version: str
        debug: bool = False
        max_connections: int = 100
        allowed_hosts: List[str] = field(default_factory=list)
        database_url: Optional[str] = None

    schema = DataclassSchema(
        APIConfig,
        {
            'name': All(str, Length(min=1, max=50), Match(r'^[a-zA-Z][a-zA-Z0-9_-]*$')),
            'version': Match(r'^\d+\.\d+\.\d+$'),  # Semantic versioning
            'max_connections': Range(min=1, max=10000),
            'allowed_hosts': [All(str, Length(min=1))],
            'database_url': Any(None, All(str, Length(min=1))),
        },
    )

    # Test complex configuration
    result = schema(
        {
            'name': 'my-awesome-api',
            'version': '1.2.3',
            'debug': True,
            'max_connections': 500,
            'allowed_hosts': ['localhost', '127.0.0.1', 'api.example.com'],
            'database_url': 'postgresql://user:pass@localhost:5432/mydb',
        }
    )

    print(f"API Config: {result}")
    print(f"Debug mode: {result.debug}")
    print(f"Allowed hosts: {result.allowed_hosts}")
    print()


def example_backward_compatibility():
    """Demonstrate that dataclass support doesn't break existing functionality."""
    print("=== Backward Compatibility ===")

    # Regular voluptuous schema still works
    regular_schema = Schema(
        {'name': str, 'age': Range(min=0, max=150), 'email': Email()}
    )

    result = regular_schema(
        {'name': 'John Doe', 'age': 30, 'email': 'john@example.com'}
    )

    print(f"Regular schema result: {result}")
    print(f"Regular schema type: {type(result)}")
    print()


def main():
    """Run all examples."""
    print("Voluptuous Dataclasses Support Examples")
    print("=" * 50)
    print()

    example_basic_dataclass()
    example_dataclass_with_constraints()
    example_nested_dataclasses()
    example_dataclass_with_lists()
    example_create_dataclass_schema_function()
    example_dataclass_detection()
    example_complex_validation()
    example_backward_compatibility()

    print("=" * 50)
    print("All examples completed successfully!")
    print()
    print("Key benefits of dataclasses support:")
    print("- Automatic schema generation from dataclass definitions")
    print("- Type safety with automatic type validation")
    print("- Seamless integration with existing voluptuous validators")
    print("- Support for default values and default factories")
    print("- Full backward compatibility with existing voluptuous features")


if __name__ == "__main__":
    main()
