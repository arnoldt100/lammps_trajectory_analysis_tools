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
	ValueObject,
	ValueSemantics,
	ValueValidationError,
)

__all__ = [
	"BuilderKeyError",
	"BuilderRegistrationError",
	"BuilderRegistry",
	"ImmutableValue",
	"MutableValue",
	"SupportsBuild",
	"ValueObject",
	"ValueSemantics",
	"ValueValidationError",
]
