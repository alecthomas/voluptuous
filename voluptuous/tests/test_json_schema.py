"""Tests for JSON Schema export functionality."""

import pytest

from voluptuous import (
    All,
    Any,
    Clamp,
    Coerce,
    Date,
    Datetime,
    Email,
    ExactSequence,
    In,
    Length,
    Match,
    Optional,
    Range,
    Required,
    Schema,
    Url,
    to_json_schema,
)


class TestBasicTypes:
    """Test conversion of basic Python types to JSON Schema."""

    def test_primitive_types(self):
        """Test conversion of primitive Python types."""
        assert to_json_schema(Schema(str)) == {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "string",
        }

        assert to_json_schema(Schema(int)) == {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "integer",
        }

        assert to_json_schema(Schema(float)) == {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "number",
        }

        assert to_json_schema(Schema(bool)) == {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "boolean",
        }

    def test_literal_values(self):
        """Test conversion of literal values."""
        schema = to_json_schema(Schema("hello"))
        assert schema["const"] == "hello"

        schema = to_json_schema(Schema(42))
        assert schema["const"] == 42

    def test_none_type(self):
        """Test conversion of None type."""
        schema = to_json_schema(Schema(None))
        assert schema["type"] == "null"


class TestObjectSchemas:
    """Test conversion of dictionary/object schemas."""

    def test_simple_object(self):
        """Test simple object schema conversion."""
        voluptuous_schema = Schema({'name': str, 'age': int})

        json_schema = voluptuous_schema.to_json_schema()

        assert json_schema["type"] == "object"
        assert "properties" in json_schema
        assert json_schema["properties"]["name"]["type"] == "string"
        assert json_schema["properties"]["age"]["type"] == "integer"
        assert json_schema["additionalProperties"] is False

    def test_required_optional_keys(self):
        """Test Required and Optional markers."""
        voluptuous_schema = Schema(
            {
                Required('name'): str,
                Optional('age'): int,
                Optional('email', default='none@example.com'): str,
            }
        )

        json_schema = voluptuous_schema.to_json_schema()

        assert json_schema["required"] == ["name"]
        assert "name" in json_schema["properties"]
        assert "age" in json_schema["properties"]
        assert "email" in json_schema["properties"]
        assert json_schema["properties"]["email"]["default"] == "none@example.com"

    def test_nested_objects(self):
        """Test nested object schemas."""
        voluptuous_schema = Schema(
            {
                'user': {
                    Required('name'): str,
                    Optional('profile'): {'bio': str, 'age': int},
                }
            }
        )

        json_schema = voluptuous_schema.to_json_schema()

        user_schema = json_schema["properties"]["user"]
        assert user_schema["type"] == "object"
        assert user_schema["required"] == ["name"]

        profile_schema = user_schema["properties"]["profile"]
        assert profile_schema["type"] == "object"
        assert "bio" in profile_schema["properties"]
        assert "age" in profile_schema["properties"]


class TestArraySchemas:
    """Test conversion of array/list schemas."""

    def test_simple_array(self):
        """Test simple array schema."""
        schema = to_json_schema(Schema([str]))
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"

    def test_mixed_array(self):
        """Test array with multiple types."""
        schema = to_json_schema(Schema([str, int, bool]))
        assert schema["type"] == "array"
        assert "prefixItems" in schema
        assert len(schema["prefixItems"]) == 3
        assert schema["prefixItems"][0]["type"] == "string"
        assert schema["prefixItems"][1]["type"] == "integer"
        assert schema["prefixItems"][2]["type"] == "boolean"
        assert schema["items"] is False

    def test_set_schema(self):
        """Test set schema conversion."""
        schema = to_json_schema(Schema({str}))
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"
        assert schema["uniqueItems"] is True


class TestValidators:
    """Test conversion of voluptuous validators."""

    def test_range_validator(self):
        """Test Range validator conversion."""
        schema = to_json_schema(Schema(Range(min=1, max=100)))
        assert schema["type"] == "number"
        assert schema["minimum"] == 1
        assert schema["maximum"] == 100

    def test_length_validator(self):
        """Test Length validator conversion."""
        schema = to_json_schema(Schema(Length(min=2, max=50)))
        assert schema["minLength"] == 2
        assert schema["maxLength"] == 50

    def test_in_validator(self):
        """Test In validator conversion."""
        schema = to_json_schema(Schema(In(['red', 'green', 'blue'])))
        assert schema["enum"] == ['red', 'green', 'blue']

    def test_match_validator(self):
        """Test Match validator conversion."""
        schema = to_json_schema(Schema(Match(r'^[a-z]+$')))
        assert schema["type"] == "string"
        assert schema["pattern"] == '^[a-z]+$'

    def test_email_validator(self):
        """Test Email validator conversion."""
        schema = to_json_schema(Schema(Email()))
        assert schema["type"] == "string"
        assert schema["format"] == "email"

    def test_url_validator(self):
        """Test Url validator conversion."""
        schema = to_json_schema(Schema(Url()))
        assert schema["type"] == "string"
        assert schema["format"] == "uri"

    def test_date_validator(self):
        """Test Date validator conversion."""
        schema = to_json_schema(Schema(Date()))
        assert schema["type"] == "string"
        assert schema["format"] == "date"

    def test_datetime_validator(self):
        """Test Datetime validator conversion."""
        schema = to_json_schema(Schema(Datetime()))
        assert schema["type"] == "string"
        assert schema["format"] == "date-time"

    def test_coerce_validator(self):
        """Test Coerce validator conversion."""
        schema = to_json_schema(Schema(Coerce(int)))
        assert schema["type"] == "integer"

    def test_clamp_validator(self):
        """Test Clamp validator conversion."""
        schema = to_json_schema(Schema(Clamp(min=0, max=1)))
        assert schema["type"] == "number"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 1


class TestCompositeValidators:
    """Test conversion of composite validators like All and Any."""

    def test_all_validator(self):
        """Test All validator conversion."""
        schema = to_json_schema(Schema(All(str, Length(min=1, max=100))))
        assert "allOf" in schema
        assert len(schema["allOf"]) == 2
        assert schema["allOf"][0]["type"] == "string"
        assert schema["allOf"][1]["minLength"] == 1
        assert schema["allOf"][1]["maxLength"] == 100

    def test_any_validator(self):
        """Test Any validator conversion."""
        schema = to_json_schema(Schema(Any(str, int)))
        assert "anyOf" in schema
        assert len(schema["anyOf"]) == 2
        assert schema["anyOf"][0]["type"] == "string"
        assert schema["anyOf"][1]["type"] == "integer"

    def test_exact_sequence(self):
        """Test ExactSequence validator conversion."""
        schema = to_json_schema(Schema(ExactSequence([str, int, bool])))
        assert schema["type"] == "array"
        assert "prefixItems" in schema
        assert len(schema["prefixItems"]) == 3
        assert schema["items"] is False
        assert schema["minItems"] == 3
        assert schema["maxItems"] == 3


class TestComplexSchemas:
    """Test conversion of complex, real-world schemas."""

    def test_user_profile_schema(self):
        """Test a realistic user profile schema."""
        voluptuous_schema = Schema(
            {
                Required('username'): All(
                    str, Length(min=3, max=20), Match(r'^[a-zA-Z0-9_]+$')
                ),
                Required('email'): Email(),
                Optional('age'): Range(min=13, max=120),
                Optional('profile'): {
                    Optional('bio'): All(str, Length(max=500)),
                    Optional('website'): Url(),
                    Optional('tags'): [str],
                },
                Optional('preferences'): {
                    'theme': In(['light', 'dark']),
                    'notifications': bool,
                },
            }
        )

        json_schema = voluptuous_schema.to_json_schema()

        # Check top-level structure
        assert json_schema["type"] == "object"
        assert set(json_schema["required"]) == {"username", "email"}

        # Check username validation
        username_schema = json_schema["properties"]["username"]
        assert "allOf" in username_schema

        # Check email validation
        email_schema = json_schema["properties"]["email"]
        assert email_schema["format"] == "email"

        # Check nested profile object
        profile_schema = json_schema["properties"]["profile"]
        assert profile_schema["type"] == "object"

        # Check preferences
        prefs_schema = json_schema["properties"]["preferences"]
        assert prefs_schema["properties"]["theme"]["enum"] == ['light', 'dark']
        assert prefs_schema["properties"]["notifications"]["type"] == "boolean"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_schema(self):
        """Test empty schema conversion."""
        schema = to_json_schema(Schema({}))
        assert schema["type"] == "object"
        assert schema["properties"] == {}

    def test_callable_validator(self):
        """Test custom callable validator."""

        def custom_validator(value):
            return value

        schema = to_json_schema(Schema(custom_validator))
        assert "description" in schema
        assert "custom_validator" in schema["description"]
