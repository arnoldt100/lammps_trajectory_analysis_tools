"""Reusable, domain-neutral design-pattern templates."""

from .value_semantics import (
	ImmutableValue,
	MutableValue,
	ValueObject,
	ValueSemantics,
	ValueValidationError,
)

__all__ = [
	"ImmutableValue",
	"MutableValue",
	"ValueObject",
	"ValueSemantics",
	"ValueValidationError",
]
