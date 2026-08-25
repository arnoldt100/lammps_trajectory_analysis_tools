#! /usr/bin/env python3
"""Provide the mutable, worker-local array accumulator.

``ArrayAccumulator`` is the working object: it accepts contributions through
``accumulate()``, can be cleared with ``reset()``, and exposes the current
values through ``finalize()``. Its private
``ArrayAccumulatorState`` owns the mutable arrays, while
``ArrayAccumulatorBehavior`` performs the accumulator-specific operations.

Calling ``to_value()`` creates an independent ``ArrayAccumulatorValue``
snapshot. That value is defined in the companion
``array_accumulator_value`` module and owns separate read-only copies for
observation and reduction. The two classes are therefore a mutable producer
and an immutable snapshot, not two interchangeable accumulator
implementations.

The mutable wrapper corresponds to the value-semantics template
``StateValueObjectMutable``; the concrete state and behavior remain specific
to array accumulation.
"""

from __future__ import annotations

# Python standard library imports
from typing import TYPE_CHECKING, Any

import numpy as np

from .accumulator_protocol import AccumulatorProtocol
from .array_accumulator_behavior import ArrayAccumulatorBehavior
from .array_accumulator_state import ArrayAccumulatorState

if TYPE_CHECKING:
    from .array_accumulator_value import ArrayAccumulatorValue

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
        self._name = name
        self._state = ArrayAccumulatorState(dtype, capacity, initial_value)
        self._behavior = ArrayAccumulatorBehavior()

    def _active_view(self) -> np.ndarray:
        """Return the region of the buffer."""
        return self._behavior.finalize(self._state)

    def __str__(self) -> str:
        message = f"\n{self._name}\n"
        values = self._active_view()
        for counter in range(self.capacity):
            message += f"{self._name}[{counter}] = {values[counter]}\n"
        message += f"accumulator sum, = {np.sum(values)}\n"
        return message

    def accumulate(self, index: int, value: T) -> None:
        """Adds a single value of type T to the accumulator.

        Args:
            index: The index at which to accumulate the value.
            value: The value to accumulate at the specified index.
        """
        self._behavior.accumulate(self._state, index, value)

    def reset(self) -> None:
        """Reset the accumulator in place.

        Sets every entry in the internal buffer to the configured initial value and
        sets all counters to zero, preserving capacity and dtype.

        Returns:
            None.
        """
        self._behavior.reset(self._state)

    @property
    def dtype(self) -> np.dtype:
        """The NumPy dtype of the accumulator elements."""
        return self._state.dtype

    @property
    def capacity(self) -> int:
        """The maximum number of elements the accumulator can hold."""
        return self._state.capacity

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

    def to_value(self) -> ArrayAccumulatorValue:
        """Return an independent immutable snapshot of accumulated state."""
        return self._behavior.to_value(self._state, name=self._name)