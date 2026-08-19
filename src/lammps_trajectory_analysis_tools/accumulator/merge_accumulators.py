#! /usr/bin/env python3
"""Provides helper functions for merging ArrayAccumulator instances."""

# Python standard library imports
from typing import TypeVar

# Local Library package imports
import numpy as np

from lammps_trajectory_analysis_tools.accumulator.array_accumulator import ArrayAccumulator
from lammps_trajectory_analysis_tools.accumulator.accumulator_protocol import (
    AccumulatorProtocol,
)

T = TypeVar("T", np.float64, np.int32, np.complex64)


def merge_array_accumulators(
    lhs: AccumulatorProtocol[T],
    rhs: AccumulatorProtocol[T],
    name: str = "Merged Accumulator",
) -> ArrayAccumulator[T]:
    """Merge two ArrayAccumulator instances by element-wise summation.

    The two accumulators must use the same global capacity. The inputs are not
    mutated and the returned accumulator is a new dense accumulator.

    Args:
        lhs: The left-hand accumulator.
        rhs: The right-hand accumulator.
        name: Optional descriptive name for the resulting accumulator.

    Returns:
        A new ArrayAccumulator whose buffer is the element-wise sum of lhs
        and rhs, with capacity equal to the larger of the two inputs.

    Raises:
        TypeError: If the two accumulators have incompatible dtypes.
        ValueError: If the two accumulators have different capacities.
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

    merged_capacity = lhs.capacity
    dtype: np.dtype = lhs.dtype

    combined: np.ndarray = np.asarray(lhs.finalize()) + np.asarray(rhs.finalize())

    merged: ArrayAccumulator[T] = ArrayAccumulator(
        dtype=dtype, capacity=merged_capacity, name=name
    )
    for i in range(merged_capacity):
        merged.accumulate(i, combined[i])

    return merged