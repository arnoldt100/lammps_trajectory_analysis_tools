"""Numeric owned-object example for value-semantics templates."""

from __future__ import annotations


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
