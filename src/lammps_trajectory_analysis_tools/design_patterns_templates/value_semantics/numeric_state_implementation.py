"""Numeric owned-object example for value-semantics templates."""

from __future__ import annotations

from typing import Any, Self

class NumericStateImplementation:
    """Concrete owned object with a private numeric value."""

    __slots__ = ("_value",)

    def __init__(self, value: int) -> None:
        self._value = value

    @property
    def value(self) -> int:
        """Return the object's numeric value."""
        return self._value

    def dummy_method(self) -> None:
        """Print the object's numeric value as an example behavior."""
        print(self._value)

    def validate_state(self) -> None:
        """Validate that the value is an integer."""
        if not isinstance(self._value, int):
            raise ValueError("value must be an integer")

    def replace(self, changes: Any) -> Self:
        """Return a new object with a replacement numeric value."""
        return type(self)(changes)

    def update(self, changes: Any) -> None:
        """Replace the numeric value in place."""
        self._value = changes
