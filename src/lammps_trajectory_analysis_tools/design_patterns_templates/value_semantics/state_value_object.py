"""Concrete state-bearing value-object implementation.

This module contains the public concrete implementation. The helper functions it
uses for hashing are intentionally private support utilities and are not part of
this package's public contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Self

from .value_object_helpers import _hashable_state
from .value_object_interface import ValueObjectInterface
from .validation import validate_state


class StateValueObject(ValueObjectInterface):
    """Concrete state-bearing implementation of the value-object contract.

    Unlike ``ValueObjectInterface``, this class owns the actual private state
    and validates it during construction and replacement. This is the concrete
    implementation that stores data; the interface remains data-free.
    """

    __slots__ = ("_state",)

    def __init__(self, state: Mapping[str, Any]) -> None:
        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping")
        if any(not isinstance(name, str) or not name for name in state):
            raise ValueError("state field names must be non-empty strings")

        copied_state = deepcopy(dict(state))
        self._validate(copied_state)
        self._state = copied_state

    @classmethod
    def _validate(cls, state: Mapping[str, Any]) -> None:
        """Validate state before it becomes part of a value object."""
        validate_state(state)

    @property
    def state(self) -> Mapping[str, Any]:
        """Return a defensive copy of the named value state."""
        return deepcopy(self._state)

    def replace(self, **changes: Any) -> Self:
        """Return a new instance with ``changes`` applied to its state."""
        updated_state = self.state
        updated_state.update(changes)
        return type(self)(updated_state)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._state == other._state

    def __repr__(self) -> str:
        return f"{type(self).__name__}(state={self._state!r})"

    def __hash__(self) -> int:
        try:
            return hash((type(self), _hashable_state(self._state)))
        except TypeError as error:
            raise TypeError("value state contains an unhashable value") from error
