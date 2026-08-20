"""Reusable, domain-neutral design-pattern templates."""

from .builder import (
	BuilderKeyError,
	BuilderRegistrationError,
	BuilderRegistry,
	SupportsBuild,
)
from .value_semantics import (
	StateValueObjectImmutable,
	StateValueObjectMutable,
	ValueSemantics,
	ValueValidationError,
)

__all__ = [
	"BuilderKeyError",
	"BuilderRegistrationError",
	"BuilderRegistry",
	"StateValueObjectImmutable",
	"StateValueObjectMutable",
	"SupportsBuild",
	"ValueSemantics",
	"ValueValidationError",
]
