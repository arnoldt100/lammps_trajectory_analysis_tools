"""Protocols describing the common value-semantics surface."""

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

    def replace_state(self, state: Any, changes: Any) -> Any:
        """Return a replacement state after applying changes."""
        ...

    def update_state(self, state: Any, changes: Any) -> Any:
        """Return an updated state after applying changes."""
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
        """Demonstrate behavior delegated for an owned object."""
        ...


class OwnedObjectProtocol(Protocol):
    """Contract for an owned object that validates its own state."""

    def validate_state(self) -> None:
        """Validate the object's internal state."""
        ...

    def replace(self, changes: Any) -> Self:
        """Return a new object with changes applied."""
        ...

    def update(self, changes: Any) -> None:
        """Apply changes to the object in place."""
        ...

@runtime_checkable
class ValueSemantics(Protocol):
    """Minimal protocol for an object whose identity is its value state."""

    @property
    def state(self) -> Any:
        """Return the object's named value state."""
        ...

    def replace(self, changes: Any) -> Self:
        """Return a new value with the requested state changes."""
        ...
