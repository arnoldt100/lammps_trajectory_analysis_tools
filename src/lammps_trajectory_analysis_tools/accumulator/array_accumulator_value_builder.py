"""Builder for immutable array accumulator values."""

import numpy as np

from .array_accumulator_value import ArrayAccumulatorValue


class ArrayAccumulatorValueBuilder:
    """Build independent immutable ``ArrayAccumulatorValue`` instances."""

    def __call__(
        self,
        dtype: np.dtype | type,
        values: np.ndarray,
        counters: np.ndarray,
        name: str = "Accumulator Value",
    ) -> ArrayAccumulatorValue:
        """Construct an immutable value from copied input arrays."""
        return ArrayAccumulatorValue(
            dtype=dtype,
            values=values,
            counters=counters,
            name=name,
        )


array_accumulator_value_builder_key = "ArrayAccumulatorValue"