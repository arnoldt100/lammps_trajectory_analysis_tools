"""Internal helper functions for value-object implementations.

These utilities are intentionally support-only functions. They are not part of
 the public value-semantics API and should only be used by concrete
value-object implementations that need deterministic hashing or placeholder
behaviors.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def free_dummy_method(state: Mapping[str, Any], *args: Any, **kwargs: Any) -> Any:
    """Placeholder free-function implementation for dummy_method semantics.

    The value object delegates to this helper so the actual behavior can be
    implemented separately from the concrete object API.
    """
    return None


def _hashable_state(state: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Return a deterministic hashable representation of value state.

    This helper is private to the value-object implementation. Callers should
    not depend on it as a public API.
    """
    return tuple(sorted((name, _hashable_value(value)) for name, value in state.items()))


def _hashable_value(value: Any) -> Any:
    """Return the input unchanged when it is already hashable.

    This helper is an internal implementation detail for hashing value objects.
    It is not a public utility for external callers.
    """
    hash(value)
    return value
