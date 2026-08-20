"""Internal hashing helpers for value-object implementations.

These functions are intentionally private support utilities. They are not part
of the public value-semantics API and should only be used by the concrete
value-object implementation classes that require deterministic hashing.
"""

from __future__ import annotations

from typing import Any


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
