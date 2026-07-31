---
applyTo: "tests/**/*.py"
---
# Pytest instructions

## Testing Standards
You must strictly enforce the following patterns when generating, refactoring, or optimizing tests in this repository:

### 1. Pytest Framework Requirements
* **Framework**: Use `pytest` exclusively. Never generate or use standard library `unittest.TestCase` boilerplate or other testing frameworks.
* **Function Names**: Test functions must begin with the `test_` prefix (e.g., `test_user_profile_creation`).
* **Assertions**: Use plain Python `assert` statements (e.g., `assert item is True`). Do not use legacy methods like `self.assertEqual()` or `self.assertTrue()`.
* **Fixtures**: Leverage `pytest` fixtures for setup and teardown logic instead of `setUp` or `tearDown` methods.

#### ❌ Incorrect (Unittest Format)
```python
import unittest

class TestUser(unittest.TestCase):
    def test_name(self):
        self.assertEqual(get_name(), "Alice")
```

####  Correct (Pytest Format)
```python
import pytest

def test_name():
    assert get_name() == "Alice"
```

