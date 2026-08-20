"""Compatibility state-bearing value-object implementation."""

from __future__ import annotations

from .state_value_object_immutable import StateValueObjectImmutable


class StateValueObject(StateValueObjectImmutable):
    """Compatibility base for the former state value object."""
