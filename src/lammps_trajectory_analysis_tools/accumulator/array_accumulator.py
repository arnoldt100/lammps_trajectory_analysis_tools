#! /usr/bin/env python3
"""Defines a bounded accumulator designed for a fixed sequence of elements."""

# Python standard library imports
from typing import Any

import numpy as np

from .accumulator_protocol import AccumulatorProtocol

class ArrayAccumulator[T](AccumulatorProtocol[T]):
    """ A bounded accumulator for a fixed sequence of elements. """
    def __init__(
        self,
        dtype: np.dtype | type,
        capacity: int = 100,
        initial_value: Any = 0.00,
        name: str = "Generic Accumulator",
    ) -> None:
        """ Initialize the accumulator with a specified data type, capacity, and initial value.

        Args:
            dtype: The data type of the accumulator elements.
            capacity: The maximum number of elements the accumulator can hold.
            initial_value: The initial value for all elements in the accumulator.
            name: A descriptive name for the accumulator.
        """
        self._dtype: np.dtype = self._coerce_dtype(dtype)
        self._capacity: np.int32 = self._validate_capacity(capacity)
        self._name = name

        # Pre-allocate memory block
        self._buffer: np.ndarray = np.empty(self._capacity, dtype=self._dtype)
        self._intial_value = self._coerce_value(initial_value)
        self._buffer[:] = self._intial_value
        self._counters : np.ndarray = np.zeros(self._capacity, dtype=np.int32)
 

    @staticmethod
    def _coerce_dtype(dtype: np.dtype | type) -> np.dtype:
        """Normalize incoming dtype to a NumPy dtype instance."""
        return np.dtype(dtype)

    @staticmethod
    def _validate_capacity(capacity: int) -> np.int32:
        """Validate and normalize storage capacity."""
        normalized_capacity = np.int32(capacity)
        if normalized_capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        return normalized_capacity

    def _coerce_value(self, value: Any) -> T:
        """Coerce values to the configured dtype."""
        return self._dtype.type(value)

    def _validate_index(self, index: int) -> np.int32:
        """Validate and normalize an index into the backing array."""
        normalized_index = np.int32(index)
        if normalized_index < 0:
            raise IndexError("index must be non-negative")
        if normalized_index >= self._capacity:
            raise IndexError("index exceeds accumulator capacity")
        return normalized_index

    def _active_view(self) -> np.ndarray:
        """Return the region of the buffer."""
        return self._buffer[: self._capacity]

    def __str__(self) -> str:
        message = f"\n{self._name}\n"
        for counter in range(self._capacity):
            message += f"{self._name}[{counter}] = {self._buffer[counter]}\n"
        message += f"accumulator sum, = {np.sum(self._buffer)}\n"
        return message

    def accumulate(self, index: int, value: T) -> None:
        """Adds a single value of type T to the accumulator.

        Args:
            index: The index at which to accumulate the value.
            value: The value to accumulate at the specified index.
        """
        validated_index = self._validate_index(index)
        self._buffer[validated_index] += self._coerce_value(value)
        self._counters[validated_index] += 1

    def reset(self):
        """Reset the accumulator in place.

        Sets every entry in the internal buffer to the configured initial value and
        sets all counters to zero, preserving capacity and dtype.

        Returns:
            None.
        """
        self._buffer[:] = self._intial_value
        self._counters[:] = 0

    @property
    def dtype(self) -> np.dtype:
        """The NumPy dtype of the accumulator elements."""
        return self._dtype

    @property
    def capacity(self) -> int:
        """The maximum number of elements the accumulator can hold."""
        return int(self._capacity)

    @property
    def name(self) -> str:
        """The descriptive name of the accumulator."""
        return self._name

    def finalize(self) -> np.ndarray:
        """Returns a typed view of the actual collected data.

        Returns:
            A NumPy array view of the accumulated data, limited to the populated
            region.
        """
        return self._active_view()