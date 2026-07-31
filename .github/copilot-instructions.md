# GitHub Copilot Engineering Standards

## Python Architecture & Coding Standards
You must strictly enforce the following patterns when writing, refactoring, or reviewing Python code in this repository:

### 1. Private Class Data Attributes
* **Rule**: All data attributes on Python classes must be strictly treated as private or protected. 
* **Convention**: Prefix every single class-level and instance-level data attribute with a single leading underscore `_`.
* **Accessors**: Never allow external direct modification of data attributes. If external access is required, expose them strictly using `@property` getter methods and setter decorators.

#### ❌ Incorrect (Public Attributes)
```python
class UserProfile:
    def __init__(self, username, email):
        self.username = username  # Error: Should be private
        self.email = email        # Error: Should be private
```

####  Correct (Enforced Private Attributes)
```python
class UserProfile:
    def __init__(self, username, email):
        self._username = username  # Correct: Prefixed with underscore
        self._email = email        # Correct: Prefixed with underscore

    @property
    def username(self):
        return self._username
```

### 2. General Python Rules
* **Type Hints**: Always add explicit type hints to all function signatures, parameters, and return types.
* **Docstrings**: Include Google-style docstrings for every class and public method.

