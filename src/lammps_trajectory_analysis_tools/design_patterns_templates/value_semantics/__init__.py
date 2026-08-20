"""Templates for implementing value-oriented domain objects."""

from .immutable_value import ImmutableValue
from .mutable_value import MutableValue
from .protocols import ValueSemantics
from .state_value_object import StateValueObject
from .validation import ValueValidationError
from .value_object import ValueObject
from .value_object_interface import ValueObjectInterface

__all__ = [
    "ImmutableValue",
    "MutableValue",
    "StateValueObject",
    "ValueObject",
    "ValueObjectInterface",
    "ValueSemantics",
    "ValueValidationError",
]
