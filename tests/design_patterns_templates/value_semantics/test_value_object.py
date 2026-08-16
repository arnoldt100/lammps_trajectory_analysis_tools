import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics import (
    ImmutableValue,
    MutableValue,
    ValueObject,
    ValueSemantics,
    ValueValidationError,
)


class PositiveValue(MutableValue):
    @classmethod
    def _validate(cls, state):
        if state.get("amount", 0) <= 0:
            raise ValueValidationError("amount must be positive")


def test_equal_state_is_equal_for_distinct_instances():
    first = ValueObject({"name": "sample", "values": [1, 2]})
    second = ValueObject({"name": "sample", "values": [1, 2]})

    assert first == second
    assert first is not second


def test_different_state_is_not_equal():
    first = ValueObject({"name": "first"})
    second = ValueObject({"name": "second"})

    assert first != second


def test_replace_returns_new_value_without_mutating_original():
    original = ValueObject({"name": "before", "count": 1})

    replacement = original.replace(name="after")

    assert original.state == {"name": "before", "count": 1}
    assert replacement.state == {"name": "after", "count": 1}
    assert replacement is not original


def test_state_is_defensively_copied():
    original = ValueObject({"values": [1, 2]})
    exposed_state = original.state
    exposed_state["values"].append(3)

    assert original.state == {"values": [1, 2]}


def test_invalid_field_name_is_rejected():
    with pytest.raises(ValueError, match="field names"):
        ValueObject({"": 1})


def test_subclass_validation_is_applied_on_construction_and_replacement():
    value = PositiveValue({"amount": 2})

    with pytest.raises(ValueValidationError, match="positive"):
        value.replace(amount=0)


def test_hashing_supports_hashable_state():
    first = ValueObject({"name": "sample", "count": 1})
    second = ValueObject({"name": "sample", "count": 1})

    assert hash(first) == hash(second)


def test_hashing_rejects_unhashable_state():
    value = ValueObject({"values": [1, 2]})

    with pytest.raises(TypeError, match="unhashable"):
        hash(value)


def test_value_object_conforms_to_protocol():
    value = ValueObject({"name": "sample"})

    assert isinstance(value, ValueSemantics)


def test_immutable_value_is_explicit_template():
    value = ImmutableValue({"name": "sample"})

    assert value.replace(name="updated") != value


def test_mutable_value_updates_state():
    value = MutableValue({"name": "before", "count": 1})

    value.update(name="after")

    assert value.state == {"name": "after", "count": 1}


def test_mutable_value_update_is_atomic_when_validation_fails():
    value = PositiveValue({"amount": 2})

    with pytest.raises(ValueValidationError, match="positive"):
        value.update(amount=0)

    assert value.state == {"amount": 2}


def test_mutable_value_is_not_hashable():
    with pytest.raises(TypeError):
        hash(MutableValue({"name": "sample"}))
