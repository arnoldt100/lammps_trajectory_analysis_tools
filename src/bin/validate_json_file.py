import argparse
import json
import sys
import jsonschema
from jsonschema import validate, ValidationError

def load_json_file(file_path):
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: '{file_path}' contains invalid JSON syntax. {e}", file=sys.stderr)
        sys.exit(1)

def validate_json_data(data_file, schema_file):
    """Validate a JSON file against a JSON schema file."""
    json_data = load_json_file(data_file)
    schema_data = load_json_file(schema_file)
    
    try:
        validate(instance=json_data, schema=schema_data)
        print("Success: The JSON file is valid against the schema.")
        sys.exit(0)
    except ValidationError as e:
        print(f"Validation Failed: {e.message}", file=sys.stderr)
        # Optional: Print the location of the error in the JSON structure
        print(f"Path to error: {'/'.join(str(p) for p in e.path)}", file=sys.stderr)
        sys.exit(1)
    except jsonschema.exceptions.SchemaError as e:
        print(f"Schema Error: The provided schema is invalid. {e.message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a JSON file against a JSON Schema.")
    
    # Define positional command-line arguments
    parser.add_argument("data_file", help="Path to the JSON data file to validate")
    parser.add_argument("schema_file", help="Path to the JSON Schema file")
    
    args = parser.parse_args()
    
    validate_json_data(args.data_file, args.schema_file)

