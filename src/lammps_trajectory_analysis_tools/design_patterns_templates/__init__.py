"""Reusable, domain-neutral design-pattern templates."""

from .builder import (
	BuilderKeyError,
	BuilderRegistrationError,
	BuilderRegistry,
	SupportsBuild,
)
from .value_semantics import (
	StateValueObject,
	StateValueObjectImmutable,
	StateValueObjectMutable,
	ValueSemantics,
	ValueValidationError,
)

__all__ = [
	"BuilderKeyError",
	"BuilderRegistrationError",
	"BuilderRegistry",
	"StateValueObject",
	"StateValueObjectImmutable",
	"StateValueObjectMutable",
	"SupportsBuild",
	"ValueSemantics",
	"ValueValidationError",
]
