"""Protocols describing the common value-semantics surface."""

from collections.abc import Mapping
from typing import Any, Protocol, Self, runtime_checkable


@runtime_checkable
class ValueSemantics(Protocol):
    """Minimal protocol for an object whose identity is its value state."""

    @property
    def state(self) -> Mapping[str, Any]:
        """Return the object's named value state."""
        ...

    def replace(self, **changes: Any) -> Self:
        """Return a new value with the requested state changes."""
        ...
