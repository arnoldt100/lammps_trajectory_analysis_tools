import numpy as np

from lammps_trajectory_analysis_tools.accumulator import (
    ArrayAccumulator,
    ArrayAccumulatorBuilder,
    array_accumulator_builder_key,
    array_accumulator_builder_registry,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    SupportsBuild,
)


def test_array_accumulator_builder_satisfies_builder_protocol() -> None:
    builder = ArrayAccumulatorBuilder()

    assert isinstance(builder, SupportsBuild)


def test_array_accumulator_builder_creates_independent_accumulators() -> None:
    builder = ArrayAccumulatorBuilder()

    first = builder(dtype=np.complex64, capacity=3, name="first")
    second = builder(dtype=np.complex64, capacity=3, name="second")

    assert isinstance(first, ArrayAccumulator)
    assert first is not second
    assert first.name == "first"
    assert second.name == "second"

    first.accumulate(0, 2 + 1j)

    assert first.finalize().tolist() == [(2 + 1j), 0j, 0j]
    assert second.finalize().tolist() == [0j, 0j, 0j]


def test_array_accumulator_builder_is_registered() -> None:
    assert array_accumulator_builder_registry.keys() == frozenset(
        {array_accumulator_builder_key}
    )

    accumulator = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.float64,
        capacity=2,
    )

    assert isinstance(accumulator, ArrayAccumulator)
