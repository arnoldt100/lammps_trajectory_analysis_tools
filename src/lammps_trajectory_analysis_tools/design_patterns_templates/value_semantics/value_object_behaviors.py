"""Public free functions for operating on state-value object instances.

These functions are the supported public API for applying shared behaviors to
StateValueObjectMutable / StateValueObjectImmutable instances from outside the
package, as an alternative to adding methods to every wrapper class.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .state_value_object_immutable import StateValueObjectImmutable
from .state_value_object_mutable import StateValueObjectMutable

StateValueObject = StateValueObjectMutable | StateValueObjectImmutable


def hash_state(value_object: StateValueObject) -> int:
    """Return a deterministic hash for the value object's underlying state."""
    state = value_object.state_implementations
    if isinstance(state, Mapping):
        return hash(tuple(sorted((name, _hashable(item)) for name, item in state.items())))
    return hash(state)


def invoke_dummy_method(value_object: StateValueObject, *args: Any, **kwargs: Any) -> Any:
    """Call the owned object's dummy_method through the value object's behavior."""
    return value_object.dummy_method(*args, **kwargs)


def _hashable(value: Any) -> Any:
    hash(value)
    return value
