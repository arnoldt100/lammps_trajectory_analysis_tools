"""Protocols describing the common value-semantics surface."""

from collections.abc import Mapping
from typing import Any, Protocol, Self, runtime_checkable


class StateValueBehaviorProtocol(Protocol):
    """Behavior contract used by state-value templates.

    ``dummy_method`` is intentionally a placeholder extension point for users
    adapting this template. It is not a domain-specific behavior requirement.
    """

    def copy_state(self, state: Any) -> Any:
        """Return an independent copy of state."""
        ...

    def validate_state(self, state: Any) -> None:
        """Validate state before it is stored."""
        ...

    def replace_state(self, state: Any, changes: Mapping[str, Any]) -> Any:
        """Return state with changes applied for immutable replacement."""
        ...

    def update_state(self, state: Any, changes: Mapping[str, Any]) -> Any:
        """Return updated state for an atomic mutable update."""
        ...

    def states_equal(self, left: Any, right: Any) -> bool:
        """Compare two state values."""
        ...

    def state_repr(self, state: Any) -> str:
        """Return a debugging representation of state."""
        ...

    def hash_state(self, state: Any) -> int:
        """Return a hash for state or raise when state is unhashable."""
        ...

    def dummy_method(
        self,
        owned_object: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Demonstrate where behavior for an owned object is delegated."""
        ...


@runtime_checkable
class ValueSemantics(Protocol):
    """Minimal protocol for an object whose identity is its value state."""

    @property
    def state(self) -> Any:
        """Return the object's named value state."""
        ...

    def replace(self, **changes: Any) -> Self:
        """Return a new value with the requested state changes."""
        ...
