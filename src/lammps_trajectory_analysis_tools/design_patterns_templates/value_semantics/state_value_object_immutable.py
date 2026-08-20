"""Immutable state-based value-object implementation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Self

from .value_object_helpers import _hashable_state, free_dummy_method
from .value_object_interface import ValueObjectInterface
from .validation import validate_state


class StateValueObjectImmutable(ValueObjectInterface):
    """Immutable state-based value object."""

    __slots__ = ("_state_implementations",)

    def __init__(self, state: Mapping[str, Any]) -> None:
        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping")
        if any(not isinstance(name, str) or not name for name in state):
            raise ValueError("state field names must be non-empty strings")

        copied_state = deepcopy(dict(state))
        self._validate(copied_state)
        self._state_implementations = copied_state

    @classmethod
    def _validate(cls, state: Mapping[str, Any]) -> None:
        """Validate state before it becomes part of a value object."""
        validate_state(state)

    @property
    def state_implementations(self) -> Mapping[str, Any]:
        """Return a defensive copy of the concrete state implementations."""
        return deepcopy(self._state_implementations)

    def replace(self, **changes: Any) -> Self:
        """Return a new instance with ``changes`` applied to its state."""
        updated_state = self.state_implementations
        updated_state.update(changes)
        return type(self)(updated_state)

    def dummy_method(self, *args: Any, **kwargs: Any) -> Any:
        """Placeholder interface method that delegates to the free helper."""
        return free_dummy_method(self._state_implementations, *args, **kwargs)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._state_implementations == other._state_implementations

    def __repr__(self) -> str:
        return f"{type(self).__name__}(state={self._state_implementations!r})"

    def __hash__(self) -> int:
        try:
            return hash((type(self), _hashable_state(self._state_implementations)))
        except TypeError as error:
            raise TypeError("value state contains an unhashable value") from error
