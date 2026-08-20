"""Templates for implementing value-oriented domain objects."""

from .protocols import ValueSemantics
from .validation import ValueValidationError
from .value_object import (
    ImmutableValue,
    MutableValue,
    StateValueObject,
    ValueObject,
    ValueObjectInterface,
)

__all__ = [
    "ImmutableValue",
    "MutableValue",
    "StateValueObject",
    "ValueObject",
    "ValueObjectInterface",
    "ValueSemantics",
    "ValueValidationError",
]
