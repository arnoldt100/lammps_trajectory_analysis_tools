"""Validation primitives shared by value-semantics templates."""

from collections.abc import Callable, Iterable
from typing import Any


class ValueValidationError(ValueError):
    """Raised when a value object cannot satisfy its state invariants."""


def validate_state(
    state: Any,
    *,
    validators: Iterable[Callable[[Any], None]] = (),
) -> None:
    """Validate arbitrary state with optional whole-state validators.

    Validators should raise ``ValueValidationError`` or ``ValueError`` when
    the state is invalid. They receive the complete state so cross-field
    invariants can be expressed without coupling this helper to a domain.
    """
    for validator in validators:
        try:
            validator(state)
        except ValueValidationError:
            raise
        except ValueError as error:
            raise ValueValidationError(str(error)) from error
