"""Immutable concrete state for array accumulator values."""

from __future__ import annotations

import numpy as np


class ArrayAccumulatorValueState:
    """Own a validated, read-only accumulator snapshot."""

    def __init__(
        self,
        dtype: np.dtype | type,
        values: np.ndarray,
        counters: np.ndarray,
        name: str,
    ) -> None:
        """Create an independent immutable snapshot state."""
        self._dtype = np.dtype(dtype)
        self._values = np.asarray(values, dtype=self._dtype).copy()
        self._counters = np.asarray(counters, dtype=np.int32).copy()
        self._validate()
        self._values.flags.writeable = False
        self._counters.flags.writeable = False
        self._name = name

    def _validate(self) -> None:
        """Validate the complete immutable state."""
        if self._values.ndim != 1 or self._counters.ndim != 1:
            raise ValueError("accumulator values and counters must be one-dimensional")
        if self._values.shape != self._counters.shape:
            raise ValueError("accumulator values and counters must have equal shapes")
        if self._values.size <= 0:
            raise ValueError("capacity must be a positive integer")

    @property
    def dtype(self) -> np.dtype:
        """Return the snapshot value dtype."""
        return self._dtype

    @property
    def capacity(self) -> int:
        """Return the snapshot capacity."""
        return self._values.size

    @property
    def values(self) -> np.ndarray:
        """Return a read-only view of accumulated values."""
        return self._values.view()

    @property
    def counters(self) -> np.ndarray:
        """Return a read-only view of contribution counters."""
        return self._counters.view()

    @property
    def name(self) -> str:
        """Return the descriptive snapshot name."""
        return self._name