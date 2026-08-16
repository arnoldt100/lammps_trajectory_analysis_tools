"""A small immutable value-object starting point."""

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Self

from .validation import validate_state


class ValueObject:
    """An immutable-by-interface object identified by named state.

    The input state and state returned by the public property are deep-copied
    so callers cannot mutate the value through a nested mutable object. Domain
    subclasses can override ``_validate`` to establish additional invariants.
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


class ImmutableValue(ValueObject):
    """Explicit name for the immutable value-object template."""


class MutableValue(ValueObject):
    """A value object that permits validated, atomic state updates."""

    __hash__ = None

    def update(self, **changes: Any) -> None:
        """Apply state changes only if the resulting state is valid."""
        updated_state = self.state
        updated_state.update(changes)
        self._validate(updated_state)
        self._state = updated_state


def _hashable_state(state: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Convert supported nested containers into a deterministic hash value."""
    return tuple(sorted((name, _hashable_value(value)) for name, value in state.items()))


def _hashable_value(value: Any) -> Any:
    hash(value)
    return value
