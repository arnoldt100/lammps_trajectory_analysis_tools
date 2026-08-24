import numpy as np
import pytest

from lammps_trajectory_analysis_tools.accumulator import (
    ArrayAccumulator,
    ArrayAccumulatorBehavior,
    ArrayAccumulatorBehaviorProtocol,
    ArrayAccumulatorValue,
    ArrayAccumulatorValueState,
    AccumulatorValueProtocol,
    merge_accumulator_values,
    merge_array_accumulators,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics import (
    ValueSemantics,
)


def test_accumulator_uses_additive_global_index_semantics() -> None:
    accumulator = ArrayAccumulator(
        dtype=np.float32,
        capacity=3,
        initial_value=1.0,
    )

    accumulator.accumulate(1, 2.25)
    accumulator.accumulate(1, 0.75)

    np.testing.assert_array_equal(accumulator.finalize(), [1.0, 4.0, 1.0])
    assert accumulator.capacity == 3
    assert accumulator.dtype == np.dtype(np.float32)


def test_array_accumulator_behavior_satisfies_behavior_protocol() -> None:
    assert isinstance(ArrayAccumulatorBehavior(), ArrayAccumulatorBehaviorProtocol)


def test_to_value_creates_an_independent_read_only_snapshot() -> None:
    accumulator = ArrayAccumulator(dtype=np.float64, capacity=2)
    accumulator.accumulate(0, 2.0)

    snapshot = accumulator.to_value()
    accumulator.accumulate(0, 3.0)

    assert isinstance(snapshot, ArrayAccumulatorValue)
    np.testing.assert_array_equal(snapshot.values, [2.0, 0.0])
    np.testing.assert_array_equal(snapshot.counters, [1, 0])
    assert snapshot.values.flags.writeable is False
    assert snapshot.counters.flags.writeable is False


def test_accumulator_value_owns_separate_immutable_state() -> None:
    snapshot = ArrayAccumulator(dtype=np.float64, capacity=2).to_value()

    assert isinstance(snapshot._state, ArrayAccumulatorValueState)
    assert snapshot.values.base is snapshot._state._values


def test_finalize_returns_a_read_only_view() -> None:
    accumulator = ArrayAccumulator(dtype=np.float64, capacity=2)
    accumulator.accumulate(0, 2.0)

    finalized = accumulator.finalize()

    assert finalized.flags.writeable is False
    with pytest.raises(ValueError, match="read-only"):
        finalized[0] = 9.0
    np.testing.assert_array_equal(accumulator.finalize(), [2.0, 0.0])


def test_accumulator_values_compare_by_state_and_are_unhashable() -> None:
    first = ArrayAccumulator(dtype=np.float64, capacity=2)
    second = ArrayAccumulator(dtype=np.float64, capacity=2)
    first.accumulate(1, 4.0)
    second.accumulate(1, 4.0)

    assert first.to_value() == second.to_value()
    with pytest.raises(TypeError):
        hash(first.to_value())


def test_accumulator_value_counters_participate_in_equality() -> None:
    values = np.array([2.0, 0.0])
    first = ArrayAccumulatorValue(
        dtype=np.float64,
        values=values,
        counters=np.array([1, 0], dtype=np.int32),
    )
    second = ArrayAccumulatorValue(
        dtype=np.float64,
        values=values,
        counters=np.array([2, 0], dtype=np.int32),
    )

    assert first != second


def test_immutable_value_reducer_preserves_values_and_counters() -> None:
    left = ArrayAccumulator(dtype=np.float64, capacity=2)
    right = ArrayAccumulator(dtype=np.float64, capacity=2)
    left.accumulate(0, 2.0)
    left.accumulate(0, 1.0)
    right.accumulate(1, 3.0)

    merged = merge_accumulator_values(left.to_value(), right.to_value())

    assert isinstance(merged, AccumulatorValueProtocol)
    np.testing.assert_array_equal(merged.values, [3.0, 3.0])
    np.testing.assert_array_equal(merged.counters, [2, 1])
    assert merged.values.flags.writeable is False
    assert merged.counters.flags.writeable is False


def test_accumulator_value_satisfies_value_semantics_and_replaces_state() -> None:
    accumulator = ArrayAccumulator(dtype=np.float64, capacity=2)
    accumulator.accumulate(0, 2.0)
    snapshot = accumulator.to_value()

    assert isinstance(snapshot, ValueSemantics)
    replacement_state = ArrayAccumulatorValueState(
        dtype=np.float64,
        values=np.array([8.0, 9.0]),
        counters=np.array([1, 0], dtype=np.int32),
        name="replacement",
    )
    replacement = snapshot.replace(replacement_state)

    np.testing.assert_array_equal(snapshot.values, [2.0, 0.0])
    np.testing.assert_array_equal(replacement.values, [8.0, 9.0])
    np.testing.assert_array_equal(replacement.counters, [1, 0])
    assert replacement is not snapshot


def test_accumulator_value_rejects_untyped_replacement_state() -> None:
    snapshot = ArrayAccumulator(dtype=np.float64, capacity=2).to_value()

    with pytest.raises(TypeError, match="replacement state"):
        snapshot.replace({"values": np.array([8.0, 9.0])})


@pytest.mark.parametrize("capacity", [0, -1])
def test_accumulator_rejects_non_positive_capacity(capacity: int) -> None:
    with pytest.raises(ValueError, match="capacity must be a positive integer"):
        ArrayAccumulator(dtype=np.float64, capacity=capacity)


@pytest.mark.parametrize("index", [-1, 3])
def test_accumulator_rejects_out_of_range_indices(index: int) -> None:
    accumulator = ArrayAccumulator(dtype=np.float64, capacity=3)

    with pytest.raises(IndexError):
        accumulator.accumulate(index, 1.0)


def test_reset_restores_initial_value_and_clears_accumulation() -> None:
    accumulator = ArrayAccumulator(
        dtype=np.int32,
        capacity=2,
        initial_value=4,
    )
    accumulator.accumulate(0, 3)
    accumulator.accumulate(1, 2)

    accumulator.reset()

    np.testing.assert_array_equal(accumulator.finalize(), [4, 4])


def test_merge_requires_matching_dtype_and_capacity() -> None:
    left = ArrayAccumulator(dtype=np.float64, capacity=2)
    right = ArrayAccumulator(dtype=np.float32, capacity=2)
    different_capacity = ArrayAccumulator(dtype=np.float64, capacity=3)

    with pytest.raises(TypeError, match="different dtypes"):
        merge_array_accumulators(left, right)
    with pytest.raises(ValueError, match="different capacities"):
        merge_array_accumulators(left, different_capacity)


def test_merge_does_not_mutate_inputs() -> None:
    left = ArrayAccumulator(dtype=np.float64, capacity=2)
    right = ArrayAccumulator(dtype=np.float64, capacity=2)
    left.accumulate(0, 2.0)
    right.accumulate(1, 3.0)

    merged = merge_array_accumulators(left, right)

    np.testing.assert_array_equal(merged.finalize(), [2.0, 3.0])
    np.testing.assert_array_equal(left.finalize(), [2.0, 0.0])
    np.testing.assert_array_equal(right.finalize(), [0.0, 3.0])
