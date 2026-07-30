#! /usr/bin/env python3
""" Defines a bounded accumulator designed for a fixed sequence of elements.

"""

# Python standard library imports
from typing import TypeVar, Generic, Union, Sequence

# Local Library package imports
import numpy as np

from data_types import Number, Integer

# Define a TypeVar restricted to supported NumPy types
T = TypeVar('T', Number, Integer, np.complex64)

class ArrayAccumulator(Generic[T]):
    def __init__(self, dtype: np.dtype | type, initial_capacity: int = 100) -> None:
        self.dtype: np.dtype = np.dtype(dtype)
        self.capacity: int = initial_capacity
        self.size: int = 0
        # Pre-allocate memory block
        self.buffer: np.ndarray = np.empty(self.capacity, dtype=self.dtype)

    def append(self, value: T) -> None:
        """Adds a single value of type T to the accumulator."""
        if self.size >= self.capacity:
            self._resize()
        self.buffer[self.size] = value
        self.size += 1

    def extend(self, values: Union[Sequence[T], np.ndarray]) -> None:
        """Adds an iterable or numpy array of values."""
        arr_values = np.asarray(values, dtype=self.dtype)
        num_new: int = arr_values.size
        
        while self.size + num_new > self.capacity:
            self._resize()
            
        self.buffer[self.size:self.size + num_new] = arr_values
        self.size += num_new

    def _resize(self) -> None:
        """Doubles the underlying buffer capacity when full."""
        self.capacity *= 2
        new_buffer = np.empty(self.capacity, dtype=self.dtype)
        new_buffer[:self.size] = self.buffer[:self.size]
        self.buffer = new_buffer

    def finalize(self) -> np.ndarray:
        """Returns a typed view of the actual collected data."""
        return self.buffer[:self.size]

