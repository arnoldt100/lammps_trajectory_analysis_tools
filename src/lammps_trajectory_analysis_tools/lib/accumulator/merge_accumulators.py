#! /usr/bin/env python3
"""Provides helper functions for merging ArrayAccumulator instances."""

# Python standard library imports
from typing import TypeVar

# Local Library package imports
import numpy as np

from lammps_trajectory_analysis_tools.lib.accumulator.array_accumulator import ArrayAccumulator

T = TypeVar("T", np.float64, np.int32, np.complex64)


def merge_array_accumulators(
    lhs: ArrayAccumulator[T],
    rhs: ArrayAccumulator[T],
    name: str = "Merged Accumulator",
) -> ArrayAccumulator[T]:
    """Merge two ArrayAccumulator instances by element-wise summation.

    When the two accumulators have different capacities, the smaller one is
    treated as if it were padded with zeros up to the larger capacity.

    Args:
        lhs: The left-hand accumulator.
        rhs: The right-hand accumulator.
        name: Optional descriptive name for the resulting accumulator.

    Returns:
        A new ArrayAccumulator whose buffer is the element-wise sum of lhs
        and rhs, with capacity equal to the larger of the two inputs.

    Raises:
        TypeError: If the two accumulators have incompatible dtypes.
    """
    if lhs.dtype != rhs.dtype:
        raise TypeError(
            f"Cannot merge accumulators with different dtypes: "
            f"{lhs.dtype} vs {rhs.dtype}"
        )

    merged_capacity: np.int32 = max(lhs.capacity, rhs.capacity)
    dtype: np.dtype = lhs.dtype

    lhs_padded: np.ndarray = np.zeros(merged_capacity, dtype=dtype)
    rhs_padded: np.ndarray = np.zeros(merged_capacity, dtype=dtype)
    lhs_padded[: lhs.capacity] = lhs.finalize()
    rhs_padded[: rhs.capacity] = rhs.finalize()

    combined: np.ndarray = lhs_padded + rhs_padded

    merged: ArrayAccumulator[T] = ArrayAccumulator(
        dtype=dtype, capacity=merged_capacity, name=name
    )
    for i in range(merged_capacity):
        merged.accumulate(i, combined[i])

    return merged
