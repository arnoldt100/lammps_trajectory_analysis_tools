"""Concrete mutable state for array-backed accumulators.

Value-semantics counterpart:
    Module: ``design_patterns_templates.value_semantics.concrete_state_implementation``
    Class: ``ConcreteStateImplementation``

This accumulator-specific state owns the numerical fields used by the mutable
value wrapper and follows the concrete-state implementation pattern.
"""

from typing import Any, Generic, TypeVar

import numpy as np


T = TypeVar("T")


class ArrayAccumulatorState(Generic[T]):
    """Represent mutable buffer and counter state for one array accumulator."""

    def __init__(
        self,
        dtype: np.dtype | type,
        capacity: int,
        initial_value: Any,
    ) -> None:
        """Create validated, independently owned accumulator state."""
        self._dtype = self._coerce_dtype(dtype)
        self._capacity = self._validate_capacity(capacity)
        self._buffer = np.empty(self._capacity, dtype=self._dtype)
        self._initial_value = self._coerce_value(initial_value)
        self._buffer[:] = self._initial_value
        self._counters = np.zeros(self._capacity, dtype=np.int32)

    @staticmethod
    def _coerce_dtype(dtype: np.dtype | type) -> np.dtype:
        """Normalize an incoming dtype to a NumPy dtype."""
        return np.dtype(dtype)

    @staticmethod
    def _validate_capacity(capacity: int) -> int:
        """Validate and normalize storage capacity."""
        normalized_capacity = np.int32(capacity)
        if normalized_capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        return int(normalized_capacity)

    def _coerce_value(self, value: Any) -> T:
        """Coerce a value to the configured dtype."""
        return self._dtype.type(value)

    def _validate_index(self, index: int) -> int:
        """Validate and normalize an index into the backing array."""
        normalized_index = np.int32(index)
        if normalized_index < 0:
            raise IndexError("index must be non-negative")
        if normalized_index >= self._capacity:
            raise IndexError("index exceeds accumulator capacity")
        return int(normalized_index)

    def accumulate(self, index: int, value: T) -> None:
        """Add a coerced value and contribution count at an index."""
        validated_index = self._validate_index(index)
        self._buffer[validated_index] += self._coerce_value(value)
        self._counters[validated_index] += 1

    def reset(self) -> None:
        """Restore initial values and clear contribution counts."""
        self._buffer[:] = self._initial_value
        self._counters[:] = 0

    def finalize(self) -> np.ndarray:
        """Return the current accumulated values for the owning wrapper."""
        values = self._buffer[: self._capacity].view()
        values.flags.writeable = False
        return values

    @property
    def dtype(self) -> np.dtype:
        """Return the NumPy dtype of accumulated values."""
        return self._dtype

    @property
    def capacity(self) -> int:
        """Return the number of addressable values."""
        return self._capacity
