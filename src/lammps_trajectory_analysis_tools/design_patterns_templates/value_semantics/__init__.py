"""Templates for implementing value-oriented domain objects."""

from .protocols import ValueSemantics
from .state_value_object import StateValueObject
from .state_value_object_immutable import StateValueObjectImmutable
from .state_value_object_mutable import StateValueObjectMutable
from .validation import ValueValidationError
from .value_object_interface import ValueObjectInterface

__all__ = [
    "StateValueObject",
    "StateValueObjectImmutable",
    "StateValueObjectMutable",
    "ValueObjectInterface",
    "ValueSemantics",
    "ValueValidationError",
]
