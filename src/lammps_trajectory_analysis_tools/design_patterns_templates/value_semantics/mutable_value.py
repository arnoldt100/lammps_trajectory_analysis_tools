"""Mutable concrete value-object variant."""

from __future__ import annotations

from typing import Any

from .state_value_object import StateValueObject

class MutableValue(StateValueObject):
    """Mutable value-object variant.

    This still implements the value-object contract, but adds an explicit
    in-place ``update()`` operation. The object remains value-based in equality
    and replacement semantics; mutation is just a convenience method on the
    concrete implementation.
    """

    __hash__ = None

    def update(self, **changes: Any) -> None:
        """Apply state changes only if the resulting state is valid."""
        updated_state = self.state
        updated_state.update(changes)
        self._validate(updated_state)
        self._state = updated_state
