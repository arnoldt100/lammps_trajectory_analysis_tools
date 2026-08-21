"""Concrete owned-object example for value-semantics templates."""

from __future__ import annotations

from typing import Any, Self


class ConcreteStateImplementation:
    """Concrete owned object with a private message value."""

    __slots__ = ("_message",)

    def __init__(self, message: str) -> None:
        self._message = message

    @property
    def message(self) -> str:
        """Return the object's message."""
        return self._message

    def dummy_method(self) -> None:
        """Print the object's message as an example behavior."""
        print(self._message)

    def validate_state(self) -> None:
        """Validate that the message is a non-empty string."""
        if not isinstance(self._message, str) or not self._message:
            raise ValueError("message must be a non-empty string")

    def replace(self, changes: Any) -> Self:
        """Return a new object with a replacement message."""
        return type(self)(changes)

    def update(self, changes: Any) -> None:
        """Replace the message in place."""
        self._message = changes
