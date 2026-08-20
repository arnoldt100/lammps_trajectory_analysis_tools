"""Public value-object facade for the design template package."""

from __future__ import annotations

from .state_value_object import StateValueObject


class ValueObject(StateValueObject):
    """Concrete value object implementation.

    This is the default immutable-by-default value object: equality is based on
    state and new values are created with ``replace()`` rather than mutating the
    existing instance.
    """
