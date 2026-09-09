""" Collection of JSON helpers classes, functions, etc. """

import json
import jsonschema

from jsonschema import validate
from pathlib import Path
from typing import Any, Dict, Tuple, Union

def read_json_file(file_path: Union[str, Path]) -> Any:
    """Reads a JSON file from the given path and returns its parsed content.

    Args:
        file_path: The path to the JSON file (as a string or Path object).

    Returns:
        The parsed JSON data (typically a dict or list).

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_jsonschema_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Reads a JSON Schema file from the given path and returns it as a dictionary.

    Args:
        file_path: The path to the schema file (as a string or Path object).

    Returns:
        A dictionary containing the parsed JSON schema structure.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON syntax.
        ValueError: If the file is valid JSON but does not resolve to a 
                    dictionary/object (e.g., if it's a JSON array or string).
    """
    # Reuse your existing helper to open and parse the file
    schema = read_json_file(file_path)

    # Structural check: A valid JSON schema root must be a JSON Object (dict)
    if not isinstance(schema, dict):
        raise ValueError(
            f"Invalid schema structure at '{file_path}'. "
            f"A JSON Schema must resolve to a dictionary, but got {type(schema).__name__}."
        )
    return schema


def validate_json_file(
    data_path: Union[str, Path], 
    schema_path: Union[str, Path]
) -> Tuple[bool, str]:
    """Validates a JSON data file against a JSON schema file.

    Args:
        data_path: Path to the JSON data file.
        schema_path: Path to the JSON schema file.

    Returns:
        A tuple of (is_valid, message). 
        - If valid: (True, "Validation successful")
        - If invalid: (False, "Detailed reason why validation failed")

    Raises:
        FileNotFoundError: If either file is missing.
        json.JSONDecodeError: If either file contains invalid JSON syntax.
    """
    # Load both files using your existing helpers
    data = read_json_file(data_path)
    schema = read_jsonschema_file(schema_path)

    try:
        # Validate data against schema
        validate(instance=data, schema=schema)
        return True, "Validation successful"
    except jsonschema.exceptions.ValidationError as e:
        # Return False along with the specific validation error message
        return False, e.message
    except jsonschema.exceptions.SchemaError as e:
        # Catch errors if the schema file itself is poorly written/invalid
        return False, f"Invalid JSON Schema: {e.message}"
