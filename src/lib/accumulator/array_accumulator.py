#! /usr/bin/env python3
""" Defines a bounded accumulator designed for a fixed sequence of elements.

"""

# Python standard library imports
from typing import TypeVar, Generic, Union, Sequence

# Local Library package imports
import numpy as np

from data_types import Number, Integer

# Define a TypeVar restricted to supported NumPy types
T = TypeVar('T', np.float64, np.int32, np.complex64)

class ArrayAccumulator(Generic[T]):
    def __init__(self, dtype: np.dtype | type, capacity: np.int32 = 100,
                 initial_value=0.00,
                 name="Generic Accumulator") -> None:
        self.dtype: np.dtype = np.dtype(dtype)
        self.capacity: int = capacity
        self._name = name

        # Pre-allocate memory block
        self.buffer: np.ndarray = np.empty(self.capacity, dtype=self.dtype)
        self.buffer[:] = initial_value

    def __str__(self)->str:
        message = f"{self._name}\n"
        for counter in range(self.capacity):
            message += f"{self._name}[{counter}] = {self.buffer[counter]}\n"
        return message

    def accumulate(self, index: Integer, value: T) -> None:
        """Adds a single value of type T to the accumulator."""
        self.buffer[index] += value

    def finalize(self) -> np.ndarray:
        """Returns a typed view of the actual collected data."""
        return self.buffer[:self.capacity]

