"""Templates for implementing value-oriented domain objects."""

from .protocols import ValueSemantics
from .validation import ValueValidationError
from .value_object import ImmutableValue, MutableValue, ValueObject

__all__ = [
	"ImmutableValue",
	"MutableValue",
	"ValueObject",
	"ValueSemantics",
	"ValueValidationError",
]
