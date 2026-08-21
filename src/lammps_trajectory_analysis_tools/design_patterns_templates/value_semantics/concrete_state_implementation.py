"""Concrete owned-object example for value-semantics templates."""

from __future__ import annotations


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
