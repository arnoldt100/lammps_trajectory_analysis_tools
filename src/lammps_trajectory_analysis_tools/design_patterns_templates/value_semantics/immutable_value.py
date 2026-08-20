"""Immutable concrete value-object variant."""

from __future__ import annotations

from .state_value_object import StateValueObject


class ValueObject(StateValueObject):
    """Concrete value object implementation.

    This is the default immutable-by-default value object: equality is based on
    state and new values are created with ``replace()`` rather than mutating the
    existing instance.
    """


class ImmutableValue(ValueObject):
    """Explicit immutable value-object variant.

    This is a concrete value object, not the interface type. It preserves the
    standard copy-on-write semantics and intentionally does not expose in-place
    mutation.
    """


class ImmutableValue(ValueObject):
    """Explicit immutable value-object variant.

    This is a concrete value object, not the interface type. It preserves the
    standard copy-on-write semantics and intentionally does not expose in-place
    mutation.
    """
