"""Accumulator-specific behavior for mutable array-backed state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

import numpy as np

from .array_accumulator_state import ArrayAccumulatorState

if TYPE_CHECKING:
    from .accumulator_protocol import AccumulatorProtocol
    from .accumulator_value_protocol import AccumulatorValueProtocol
    from .array_accumulator import ArrayAccumulator
    from .array_accumulator_value import ArrayAccumulatorValue


T = TypeVar("T")


@runtime_checkable
class ArrayAccumulatorBehaviorProtocol(Protocol[T]):
    """Define operations on mutable array accumulator state."""

    def accumulate(self, state: ArrayAccumulatorState[T], index: int, value: T) -> None:
        """Add a value and contribution count to an indexed state slot."""
        ...

    def finalize(self, state: ArrayAccumulatorState[T]) -> np.ndarray:
        """Return the current accumulated values."""
        ...

    def reset(self, state: ArrayAccumulatorState[T]) -> None:
        """Restore initial values and clear contribution counts."""
        ...

    def to_value(
        self,
        state: ArrayAccumulatorState[T],
        name: str = "Accumulator Value",
    ) -> ArrayAccumulatorValue:
        """Create an independent immutable snapshot of accumulator state."""
        ...


class ArrayAccumulatorBehavior(ArrayAccumulatorBehaviorProtocol[Any]):
    """Implement numerical operations for array accumulator state."""

    def accumulate(self, state: ArrayAccumulatorState[T], index: int, value: T) -> None:
        """Add a coerced value and contribution count at an index."""
        validated_index = self._validate_index(state, index)
        state._buffer[validated_index] += self._coerce_value(state, value)
        state._counters[validated_index] += 1

    def finalize(self, state: ArrayAccumulatorState[T]) -> np.ndarray:
        """Return the current accumulated values."""
        values = state._buffer[: state.capacity].view()
        values.flags.writeable = False
        return values

    def reset(self, state: ArrayAccumulatorState[T]) -> None:
        """Restore initial values and clear contribution counts."""
        state._buffer[:] = state._initial_value
        state._counters[:] = 0

    def to_value(
        self,
        state: ArrayAccumulatorState[T],
        name: str = "Accumulator Value",
    ) -> ArrayAccumulatorValue:
        """Create an independent immutable snapshot of accumulator state."""
        from .array_accumulator_value import ArrayAccumulatorValue as SnapshotType

        return SnapshotType(
            dtype=state.dtype,
            values=state._buffer,
            counters=state._counters,
            name=name,
        )

    @staticmethod
    def _coerce_value(state: ArrayAccumulatorState[T], value: Any) -> T:
        """Coerce a value to the configured dtype."""
        return state._dtype.type(value)

    @staticmethod
    def _validate_index(state: ArrayAccumulatorState[T], index: int) -> int:
        """Validate and normalize an index into the backing array."""
        normalized_index = np.int32(index)
        if normalized_index < 0:
            raise IndexError("index must be non-negative")
        if normalized_index >= state.capacity:
            raise IndexError("index exceeds accumulator capacity")
        return int(normalized_index)


def merge_accumulator_values(
    lhs: AccumulatorValueProtocol[T],
    rhs: AccumulatorValueProtocol[T],
    name: str = "Merged Accumulator Value",
) -> ArrayAccumulatorValue:
    """Merge immutable accumulator values without mutating either input.

    Args:
        lhs: The left-hand immutable accumulator value.
        rhs: The right-hand immutable accumulator value.
        name: Optional descriptive name for the merged value.

    Returns:
        A new immutable value containing summed values and counters.

    Raises:
        TypeError: If the input dtypes differ.
        ValueError: If the input capacities differ.
    """
    if lhs.dtype != rhs.dtype:
        raise TypeError(
            f"Cannot merge accumulator values with different dtypes: "
            f"{lhs.dtype} vs {rhs.dtype}"
        )
    if lhs.capacity != rhs.capacity:
        raise ValueError(
            "Cannot merge accumulator values with different capacities: "
            f"{lhs.capacity} vs {rhs.capacity}"
        )

    from .array_accumulator_value import ArrayAccumulatorValue as SnapshotType

    values = np.asarray(lhs.values) + np.asarray(rhs.values)
    counters = np.asarray(lhs.counters, dtype=np.int32) + np.asarray(
        rhs.counters,
        dtype=np.int32,
    )
    return SnapshotType(
        dtype=lhs.dtype,
        values=values,
        counters=counters,
        name=name,
    )


def merge_array_accumulators(
    lhs: ArrayAccumulator[T],
    rhs: ArrayAccumulator[T],
    name: str = "Merged Accumulator",
) -> ArrayAccumulatorValue:
    """Merge accumulators into an immutable value.

    The inputs are not mutated and the returned accumulator is a new dense
    value. Inputs must have matching dtypes and capacities.
    """
    if lhs.dtype != rhs.dtype:
        raise TypeError(
            f"Cannot merge accumulators with different dtypes: "
            f"{lhs.dtype} vs {rhs.dtype}"
        )
    if lhs.capacity != rhs.capacity:
        raise ValueError(
            "Cannot merge accumulators with different capacities: "
            f"{lhs.capacity} vs {rhs.capacity}"
        )

    return merge_accumulator_values(
        lhs.to_value(),
        rhs.to_value(),
        name=name,
    )
