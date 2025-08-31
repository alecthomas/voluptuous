"""Tests for dataclasses support in voluptuous."""

import sys

import pytest

from voluptuous import (
    All,
    Email,
    In,
    Length,
    Match,
    MultipleInvalid,
    Optional,
    Range,
    Required,
    Schema,
)

# Skip all tests if dataclasses not available
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Dataclasses require Python 3.7+"
)

# Import dataclasses and voluptuous dataclass support
if sys.version_info >= (3, 7):
    from dataclasses import dataclass, field

    from voluptuous import DataclassSchema, create_dataclass_schema, is_dataclass
else:
    # Stub imports for older Python versions
    def dataclass(cls):
        return cls

    def field(**kwargs):
        return None


class TestDataclassDetection:
    """Test dataclass detection functionality."""

    def test_is_dataclass_with_dataclass(self):
        """Test is_dataclass returns True for dataclasses."""

        @dataclass
        class Person:
            name: str
            age: int

        assert is_dataclass(Person) is True
        assert is_dataclass(Person('John', 30)) is True

    def test_is_dataclass_with_regular_class(self):
        """Test is_dataclass returns False for regular classes."""

        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age

        assert is_dataclass(Person) is False
        assert is_dataclass(Person('John', 30)) is False

    def test_is_dataclass_with_primitive_types(self):
        """Test is_dataclass returns False for primitive types."""
        assert is_dataclass(str) is False
        assert is_dataclass(int) is False
        assert is_dataclass("hello") is False
        assert is_dataclass(42) is False


class TestBasicDataclassSchema:
    """Test basic dataclass schema functionality."""

    def test_simple_dataclass_schema(self):
        """Test creating schema from simple dataclass."""

        @dataclass
        class Person:
            name: str
            age: int

        schema = DataclassSchema(Person)

        # Test valid data
        result = schema({'name': 'John', 'age': 30})
        assert isinstance(result, Person)
        assert result.name == 'John'
        assert result.age == 30

    def test_dataclass_with_defaults(self):
        """Test dataclass with default values."""

        @dataclass
        class Person:
            name: str
            age: int = 0
            active: bool = True

        schema = DataclassSchema(Person)

        # Test with all fields
        result = schema({'name': 'John', 'age': 30, 'active': False})
        assert result.name == 'John'
        assert result.age == 30
        assert result.active is False

        # Test with defaults
        result = schema({'name': 'Jane'})
        assert result.name == 'Jane'
        assert result.age == 0
        assert result.active is True

    def test_dataclass_with_default_factory(self):
        """Test dataclass with default_factory."""

        @dataclass
        class Person:
            name: str
            tags: list = field(default_factory=list)

        schema = DataclassSchema(Person)

        # Test with explicit tags
        result = schema({'name': 'John', 'tags': ['developer', 'python']})
        assert result.name == 'John'
        assert result.tags == ['developer', 'python']

        # Test with default factory
        result = schema({'name': 'Jane'})
        assert result.name == 'Jane'
        assert result.tags == []

    def test_type_validation(self):
        """Test that dataclass field types are validated."""

        @dataclass
        class Person:
            name: str
            age: int

        schema = DataclassSchema(Person)

        # Test invalid types
        with pytest.raises(MultipleInvalid):
            schema({'name': 123, 'age': 'thirty'})

        with pytest.raises(MultipleInvalid):
            schema({'name': 'John', 'age': 'thirty'})

    def test_missing_required_fields(self):
        """Test validation fails for missing required fields."""

        @dataclass
        class Person:
            name: str
            age: int

        schema = DataclassSchema(Person)

        with pytest.raises(MultipleInvalid):
            schema({'name': 'John'})  # Missing age

        with pytest.raises(MultipleInvalid):
            schema({'age': 30})  # Missing name


class TestDataclassSchemaWithConstraints:
    """Test dataclass schemas with additional validation constraints."""

    def test_additional_constraints(self):
        """Test adding validation constraints to dataclass fields."""

        @dataclass
        class Person:
            name: str
            age: int
            email: str

        schema = DataclassSchema(
            Person,
            {
                'name': Length(min=1, max=50),
                'age': Range(min=0, max=150),
                'email': Email(),
            },
        )

        # Test valid data
        result = schema({'name': 'John Doe', 'age': 30, 'email': 'john@example.com'})
        assert result.name == 'John Doe'
        assert result.age == 30
        assert result.email == 'john@example.com'

        # Test constraint violations
        with pytest.raises(MultipleInvalid):
            schema({'name': '', 'age': 30, 'email': 'john@example.com'})  # Empty name

        with pytest.raises(MultipleInvalid):
            schema(
                {'name': 'John', 'age': -5, 'email': 'john@example.com'}
            )  # Negative age

        with pytest.raises(MultipleInvalid):
            schema(
                {'name': 'John', 'age': 30, 'email': 'invalid-email'}
            )  # Invalid email

    def test_constraint_merging(self):
        """Test that constraints are properly merged with base types."""

        @dataclass
        class Product:
            name: str
            price: float
            category: str

        schema = DataclassSchema(
            Product,
            {
                'name': All(str, Length(min=1)),
                'price': All(float, Range(min=0)),
                'category': In(['electronics', 'books', 'clothing']),
            },
        )

        # Test valid data
        result = schema({'name': 'Laptop', 'price': 999.99, 'category': 'electronics'})
        assert result.name == 'Laptop'
        assert result.price == 999.99
        assert result.category == 'electronics'

        # Test constraint violations
        with pytest.raises(MultipleInvalid):
            schema(
                {'name': 'Laptop', 'price': -100, 'category': 'electronics'}
            )  # Negative price

        with pytest.raises(MultipleInvalid):
            schema(
                {'name': 'Laptop', 'price': 999.99, 'category': 'invalid'}
            )  # Invalid category

    def test_additional_fields_not_in_dataclass(self):
        """Test adding validation for fields not in the dataclass."""

        @dataclass
        class Person:
            name: str
            age: int

        schema = DataclassSchema(
            Person,
            {
                'name': Length(min=1),
                'age': Range(min=0, max=150),
                'extra_field': str,  # Not in dataclass
            },
        )

        # The extra field should be ignored since it's not in the dataclass
        result = schema({'name': 'John', 'age': 30})
        assert result.name == 'John'
        assert result.age == 30


class TestCreateDataclassSchemaFunction:
    """Test the create_dataclass_schema function."""

    def test_create_dataclass_schema_basic(self):
        """Test basic usage of create_dataclass_schema function."""

        @dataclass
        class Person:
            name: str
            age: int = 0

        schema = create_dataclass_schema(Person)

        result = schema({'name': 'John', 'age': 25})
        assert isinstance(result, Person)
        assert result.name == 'John'
        assert result.age == 25

    def test_create_dataclass_schema_with_constraints(self):
        """Test create_dataclass_schema with additional constraints."""

        @dataclass
        class User:
            username: str
            email: str
            age: int = 18

        schema = create_dataclass_schema(
            User,
            {
                'username': All(str, Length(min=3, max=20), Match(r'^[a-zA-Z0-9_]+$')),
                'email': Email(),
                'age': Range(min=13, max=120),
            },
        )

        # Test valid data
        result = schema(
            {'username': 'john_doe', 'email': 'john@example.com', 'age': 25}
        )
        assert result.username == 'john_doe'
        assert result.email == 'john@example.com'
        assert result.age == 25

        # Test invalid username
        with pytest.raises(MultipleInvalid):
            schema(
                {'username': 'jo', 'email': 'john@example.com', 'age': 25}
            )  # Too short

        with pytest.raises(MultipleInvalid):
            schema(
                {'username': 'john-doe', 'email': 'john@example.com', 'age': 25}
            )  # Invalid chars


class TestComplexDataclassSchemas:
    """Test complex dataclass scenarios."""

    def test_nested_dataclass_like_structure(self):
        """Test dataclass with nested dictionary validation."""

        @dataclass
        class Address:
            street: str
            city: str
            zipcode: str

        @dataclass
        class Person:
            name: str
            age: int
            address: dict  # We'll validate this as a nested structure

        # Create schema for Address separately
        address_schema = DataclassSchema(Address, {'zipcode': Match(r'^\d{5}$')})

        # Create schema for Person with address validation
        person_schema = DataclassSchema(
            Person,
            {
                'name': Length(min=1),
                'age': Range(min=0, max=150),
                'address': address_schema,
            },
        )

        # Test valid nested data
        result = person_schema(
            {
                'name': 'John Doe',
                'age': 30,
                'address': {
                    'street': '123 Main St',
                    'city': 'Anytown',
                    'zipcode': '12345',
                },
            }
        )

        assert result.name == 'John Doe'
        assert result.age == 30
        assert isinstance(result.address, Address)
        assert result.address.street == '123 Main St'
        assert result.address.city == 'Anytown'
        assert result.address.zipcode == '12345'

    def test_dataclass_with_list_field(self):
        """Test dataclass with list field validation."""

        @dataclass
        class Team:
            name: str
            members: list

        schema = DataclassSchema(
            Team, {'name': Length(min=1), 'members': [str]}  # List of strings
        )

        # Test valid data
        result = schema(
            {'name': 'Development Team', 'members': ['Alice', 'Bob', 'Charlie']}
        )
        assert result.name == 'Development Team'
        assert result.members == ['Alice', 'Bob', 'Charlie']

        # Test invalid member types
        with pytest.raises(MultipleInvalid):
            schema(
                {
                    'name': 'Development Team',
                    'members': ['Alice', 123, 'Charlie'],  # Invalid type in list
                }
            )


class TestErrorCases:
    """Test error cases and edge conditions."""

    def test_non_dataclass_error(self):
        """Test error when trying to create schema from non-dataclass."""

        class RegularClass:
            def __init__(self, name):
                self.name = name

        with pytest.raises(ValueError, match="is not a dataclass"):
            DataclassSchema(RegularClass)

        with pytest.raises(ValueError, match="is not a dataclass"):
            create_dataclass_schema(RegularClass)

    def test_empty_dataclass(self):
        """Test dataclass with no fields."""

        @dataclass
        class Empty:
            pass

        schema = DataclassSchema(Empty)
        result = schema({})
        assert isinstance(result, Empty)


class TestBackwardCompatibility:
    """Test that dataclass support doesn't break existing functionality."""

    def test_regular_schema_still_works(self):
        """Test that regular Schema functionality is unaffected."""
        schema = Schema({Required('name'): str, Optional('age', default=0): int})

        result = schema({'name': 'John', 'age': 30})
        assert result == {'name': 'John', 'age': 30}

        result = schema({'name': 'Jane'})
        assert result == {'name': 'Jane', 'age': 0}

    def test_object_validator_still_works(self):
        """Test that Object validator functionality is unaffected."""
        from voluptuous import Object

        class Person:
            def __init__(self, name=None, age=None):
                self.name = name
                self.age = age

        schema = Schema(Object({'name': str, 'age': int}, cls=Person))

        result = schema(Person(name='John', age=30))
        assert isinstance(result, Person)
        assert result.name == 'John'
        assert result.age == 30
