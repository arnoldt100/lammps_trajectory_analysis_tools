import numpy as np

from lammps_trajectory_analysis_tools.accumulator import (
    ArrayAccumulator,
    ArrayAccumulatorBuilder,
    ArrayAccumulatorValue,
    ArrayAccumulatorValueBuilder,
    array_accumulator_builder_key,
    array_accumulator_builder_registry,
    array_accumulator_value_builder_key,
    array_accumulator_value_builder_registry,
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


def test_array_accumulator_value_builder_satisfies_builder_protocol() -> None:
    assert isinstance(ArrayAccumulatorValueBuilder(), SupportsBuild)


def test_array_accumulator_value_builder_is_registered_and_copies_state() -> None:
    values = np.array([1.0, 2.0])
    counters = np.array([1, 2], dtype=np.int32)

    snapshot = array_accumulator_value_builder_registry.build(
        array_accumulator_value_builder_key,
        dtype=np.float64,
        values=values,
        counters=counters,
    )
    values[0] = 9.0
    counters[0] = 9

    assert isinstance(snapshot, ArrayAccumulatorValue)
    np.testing.assert_array_equal(snapshot.values, [1.0, 2.0])
    np.testing.assert_array_equal(snapshot.counters, [1, 2])
    assert array_accumulator_value_builder_registry.keys() == frozenset(
        {array_accumulator_value_builder_key}
    )
