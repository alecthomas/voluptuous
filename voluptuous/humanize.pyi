from voluptuous.schema_builder import Schema
from voluptuous.error import Error

MAX_VALIDATION_ERROR_ITEM_LENGTH: int

def humanize_error(data, validation_error: Error, max_sub_error_length: int=...) -> str: ...
def validate_with_humanized_errors(data, schema: Schema, max_sub_error_length: int=...): ...
