"""Immutable state-based value-object implementation."""

from __future__ import annotations

from typing import Any, Self

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.protocols import (
    StateValueBehaviorProtocol,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.validation import (
    validate_state,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.value_object_interface import (
    ValueObjectInterface,
)


class StateValueObjectImmutable(ValueObjectInterface):
    """Immutable state-based value object."""

    __slots__ = ("_behavior", "_state_implementations")

    def __init__(self, state: Any, behavior: StateValueBehaviorProtocol) -> None:
        self._behavior = behavior
        copied_state = behavior.copy_state(state)
        behavior.validate_state(copied_state)
        self._validate(copied_state)
        self._state_implementations = copied_state

    @classmethod
    def _validate(cls, state: Any) -> None:
        """Validate state before it becomes part of a value object."""
        validate_state(state)

    @property
    def state_implementations(self) -> Any:
        """Return a defensive copy of the concrete state implementations."""
        return self._behavior.copy_state(self._state_implementations)

    @property
    def state(self) -> Any:
        """Return a defensive copy of the value state."""
        return self.state_implementations

    def replace(self, **changes: Any) -> Self:
        """Return a new instance with ``changes`` applied to its state."""
        updated_state = self._behavior.replace_state(
            self._state_implementations,
            changes,
        )
        return type(self)(updated_state, self._behavior)

    def dummy_method(self, *args: Any, **kwargs: Any) -> Any:
        """Placeholder method that delegates to shared package behavior."""
        return self._behavior.dummy_method(
            self._state_implementations,
            *args,
            **kwargs,
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self._behavior.states_equal(
            self._state_implementations,
            other._state_implementations,
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(state="
            f"{self._behavior.state_repr(self._state_implementations)})"
        )

    def __hash__(self) -> int:
        try:
            return hash((type(self), self._behavior.hash_state(self._state_implementations)))
        except TypeError as error:
            raise TypeError("value state contains an unhashable value") from error
