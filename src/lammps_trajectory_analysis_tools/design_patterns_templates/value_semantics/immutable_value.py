"""Immutable concrete value-object variant."""

from __future__ import annotations

from .state_value_object import StateValueObject

class ImmutableValue(StateValueObject):
    """Explicit immutable value-object variant.

    This is a concrete value object, not the interface type. It preserves the
    standard copy-on-write semantics and intentionally does not expose in-place
    mutation.
    """

