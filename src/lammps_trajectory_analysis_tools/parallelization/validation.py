"""Shared validation helpers for parallelization value objects."""

from operator import index as as_index


def validate_non_negative_integer(value: int, name: str) -> int:
    """Validate and return a non-negative integer.

    Args:
        value: The value to validate.
        name: The parameter name used in error messages.

    Raises:
        TypeError: If ``value`` is not an integer.
        ValueError: If ``value`` is negative.
    """
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    try:
        normalized_value = as_index(value)
    except TypeError as error:
        raise TypeError(f"{name} must be an integer") from error
    if normalized_value < 0:
        raise ValueError(f"{name} must be non-negative")
    return normalized_value


def validate_positive_integer(value: int, name: str) -> int:
    """Validate and return a strictly positive integer."""
    normalized_value = validate_non_negative_integer(value, name)
    if normalized_value == 0:
        raise ValueError(f"{name} must be positive")
    return normalized_value