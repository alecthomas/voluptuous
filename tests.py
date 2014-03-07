from voluptuous import Schema, In


def test_in():
    """Verify that In works."""
    schema = Schema({"color": In(frozenset(["blue", "red", "yellow"]))})
    schema({"color": "blue"})
