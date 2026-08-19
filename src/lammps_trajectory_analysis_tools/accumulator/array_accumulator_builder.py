"""Builder for independent ArrayAccumulator instances."""

from typing import Any

import numpy as np

from .array_accumulator import ArrayAccumulator


class ArrayAccumulatorBuilder:
    """Build fresh, independently owned ``ArrayAccumulator`` instances."""

    def __call__(
        self,
        dtype: np.dtype | type,
        capacity: int = 100,
        initial_value: Any = 0.00,
        name: str = "Generic Accumulator",
    ) -> ArrayAccumulator[Any]:
        """Construct an accumulator from the supplied configuration."""
        return ArrayAccumulator(
            dtype=dtype,
            capacity=capacity,
            initial_value=initial_value,
            name=name,
        )
