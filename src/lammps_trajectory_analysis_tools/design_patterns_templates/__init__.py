"""Reusable, domain-neutral design-pattern templates."""

from .builder import (
	BuilderKeyError,
	BuilderRegistrationError,
	BuilderRegistry,
	SupportsBuild,
)
from .value_semantics import (
	ImmutableValue,
	MutableValue,
	StateValueObject,
	ValueSemantics,
	ValueValidationError,
)

__all__ = [
	"BuilderKeyError",
	"BuilderRegistrationError",
	"BuilderRegistry",
	"ImmutableValue",
	"MutableValue",
	"StateValueObject",
	"SupportsBuild",
	"ValueSemantics",
	"ValueValidationError",
]
