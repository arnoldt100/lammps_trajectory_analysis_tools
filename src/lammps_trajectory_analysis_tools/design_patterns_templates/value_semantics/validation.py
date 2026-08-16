"""Validation primitives shared by value-semantics templates."""

from collections.abc import Callable, Iterable, Mapping
from typing import Any


class ValueValidationError(ValueError):
    """Raised when a value object cannot satisfy its state invariants."""


def validate_state(
    state: Mapping[str, Any],
    *,
    required_fields: Iterable[str] = (),
    validators: Iterable[Callable[[Mapping[str, Any]], None]] = (),
) -> None:
    """Validate required fields and whole-state validators.

    Validators should raise ``ValueValidationError`` or ``ValueError`` when
    the state is invalid. They receive the complete state so cross-field
    invariants can be expressed without coupling this helper to a domain.
    """
    missing_fields = [field for field in required_fields if field not in state]
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueValidationError(f"missing required value fields: {missing}")

    for validator in validators:
        try:
            validator(state)
        except ValueValidationError:
            raise
        except ValueError as error:
            raise ValueValidationError(str(error)) from error
