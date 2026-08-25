"""Provide immutable snapshots of mutable array accumulators.

``ArrayAccumulatorValue`` is created by ``ArrayAccumulator.to_value()``. The
constructor defensively copies the mutable accumulator's values and counters
into a separate ``ArrayAccumulatorValueState`` and makes those arrays
read-only. Later accumulation or reset operations on the original
``ArrayAccumulator`` cannot change this snapshot.

This module is the value side of the pair: snapshots are used for stable
observation, transfer, equality, and reduction. It does not perform mutable
accumulation and does not share the worker accumulator's storage. The value
class corresponds to the value-semantics template
``StateValueObjectImmutable`` and implements the shared ``ValueSemantics``
protocol.
"""

from typing import Self

import numpy as np

from lammps_trajectory_analysis_tools.accumulator.array_accumulator_value_state import (
    ArrayAccumulatorValueState,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics import (
    ValueSemantics,
)


class ArrayAccumulatorValue(ValueSemantics):
    """Store an independent, read-only accumulator snapshot."""

    __hash__ = None

    def __init__(
        self,
        dtype: np.dtype | type,
        values: np.ndarray,
        counters: np.ndarray,
        name: str = "Accumulator Value",
    ) -> None:
        """Create a defensive, read-only copy of accumulator data."""
        self._state = ArrayAccumulatorValueState(dtype, values, counters, name)

    @property
    def values(self) -> np.ndarray:
        """Return a read-only view of accumulated values."""
        return self._state.values

    @property
    def counters(self) -> np.ndarray:
        """Return a read-only view of contribution counters."""
        return self._state.counters

    @property
    def capacity(self) -> int:
        """Return the snapshot capacity."""
        return self._state.capacity

    @property
    def dtype(self) -> np.dtype:
        """Return the snapshot value dtype."""
        return self._state.dtype

    @property
    def name(self) -> str:
        """Return the descriptive snapshot name."""
        return self._state.name

    @property
    def state(self) -> ArrayAccumulatorValueState:
        """Return the immutable concrete snapshot state."""
        return self._state

    def replace(self, state: ArrayAccumulatorValueState) -> Self:
        """Return a new value containing the supplied typed state."""
        if not isinstance(state, ArrayAccumulatorValueState):
            raise TypeError(
                "replacement state must be an ArrayAccumulatorValueState"
            )
        return type(self)(
            dtype=state.dtype,
            values=state.values,
            counters=state.counters,
            name=state.name,
        )

    def __eq__(self, other: object) -> bool:
        """Compare snapshots by dtype, capacity, values, and counters."""
        if not isinstance(other, ArrayAccumulatorValue):
            return NotImplemented
        return (
            self._state.dtype == other._state.dtype
            and self._state.capacity == other._state.capacity
            and np.array_equal(self._state.values, other._state.values)
            and np.array_equal(self._state.counters, other._state.counters)
        )

    def __repr__(self) -> str:
        """Return a concise representation of the snapshot."""
        return (
            f"{type(self).__name__}(dtype={self.dtype!r}, "
            f"capacity={self.capacity}, values={self.values!r}, "
            f"counters={self.counters!r})"
        )