"""Mutable state-based value-object implementation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Self

from .validation import validate_state
from .value_object_interface import ValueObjectInterface


class StateValueObjectMutable(ValueObjectInterface):
    """Mutable state-based value object with validated in-place updates."""

    __slots__ = ("_state",)
    __hash__ = None

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
        updated_state = dict(self.state)
        updated_state.update(changes)
        return type(self)(updated_state)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StateValueObjectMutable):
            return NotImplemented
        if type(self) is not type(other):
            return NotImplemented
        return self._state == other._state

    def __repr__(self) -> str:
        return f"{type(self).__name__}(state={self._state!r})"

    def update(self, **changes: Any) -> None:
        """Apply state changes only if the resulting state is valid."""
        updated_state = dict(self.state)
        updated_state.update(changes)
        self._validate(updated_state)
        self._state = updated_state