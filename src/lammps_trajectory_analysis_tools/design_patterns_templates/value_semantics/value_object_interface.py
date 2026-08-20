"""Interface contract for value-oriented objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Self


class ValueObjectInterface(ABC):
    """Interface contract for value-oriented objects.

    This type defines the required value semantics only: callers expect a
    state-bearing object with copy-on-write replacement behavior. It is an
    abstract interface and intentionally stores no instance data. Any concrete
    implementation must own its own private state separately.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def state(self) -> Mapping[str, Any]:
        """Return the object's named value state."""
        ...

    @abstractmethod
    def replace(self, **changes: Any) -> Self:
        """Return a new value object with state changes applied."""
        ...

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Compare this value object with another object."""
        ...

    @abstractmethod
    def __repr__(self) -> str:
        """Return a debugging representation of this value object."""
        ...
