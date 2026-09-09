import json
import pytest
from pathlib import Path
# Replace 'your_module' with the actual folder name of your module
from lammps_trajectory_analysis_tools.schemas import (
    read_json_file,
    validate_json_file,
    read_jsonschema_file,
)

def test_read_json_file_success(tmp_path: Path):
    """Test that a valid JSON file is successfully read and parsed."""
    # Arrange: Create a temporary JSON file
    test_data = {"name": "Alice", "age": 30, "skills": ["Python", "uv"]}
    file_path = tmp_path / "test_data.json"
 
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f)

    # Act: Read the file using your helper function
    result = read_json_file(file_path)

    # Assert: Verify the returned data matches the original data
    assert result == test_data
    assert result["name"] == "Alice"


def test_read_json_file_not_found():
    """Test that a FileNotFoundError is raised if the file does not exist."""
    non_existent_path = "this_file_definitely_does_not_exist.json"

    with pytest.raises(FileNotFoundError):
        read_json_file(non_existent_path)


def test_read_json_file_invalid_json(tmp_path: Path):
    """Test that a JSONDecodeError is raised if the file contains invalid JSON."""
    # Arrange: Create a file with broken JSON syntax
    invalid_content = "{ 'name': 'Alice', broken_json: true "
    file_path = tmp_path / "invalid.json"
    file_path.write_text(invalid_content, encoding="utf-8")

    # Act & Assert: Verify that parsing fails with JSONDecodeError
    with pytest.raises(json.JSONDecodeError):
        read_json_file(file_path)


@pytest.fixture
def sample_schema_file(tmp_path: Path) -> Path:
    """Fixture to create a temporary schema file."""
    schema_content = """
    {
        "$schema": "https://json-schema.org",
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "age": {"type": "integer", "minimum": 18}
        },
        "required": ["username"]
    }
    """
    schema_path = tmp_path / "user_schema.json"
    schema_path.write_text(schema_content, encoding="utf-8")
    return schema_path


def test_validate_json_file_success(tmp_path: Path, sample_schema_file: Path):
    """Test that a matching JSON file passes validation."""
    valid_data = '{"username": "dev_user", "age": 25}'
    data_path = tmp_path / "valid_data.json"
    data_path.write_text(valid_data, encoding="utf-8")

    is_valid, message = validate_json_file(data_path, sample_schema_file)

    assert is_valid is True
    assert message == "Validation successful"


def test_validate_json_file_invalid_data(tmp_path: Path, sample_schema_file: Path):
    """Test that a failing JSON file returns False and an error message."""
    # Invalid because age is under 18 and 'username' is missing
    invalid_data = '{"age": 16}'
    data_path = tmp_path / "invalid_data.json"
    data_path.write_text(invalid_data, encoding="utf-8")

    is_valid, message = validate_json_file(data_path, sample_schema_file)

    assert is_valid is False
    # The message will highlight the first missing requirement found
    assert "username" in message 

