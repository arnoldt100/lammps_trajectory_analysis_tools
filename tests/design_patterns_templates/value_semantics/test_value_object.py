from collections.abc import Mapping
from inspect import getmro
from typing import Any, Self

import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics import (
    StateValueObject,
    StateValueObjectImmutable,
    StateValueObjectMutable,
    ValueObjectInterface,
    ValueSemantics,
    ValueValidationError,
)


class PositiveValue(StateValueObjectMutable):
    @classmethod
    def _validate(cls, state):
        if state.get("amount", 0) <= 0:
            raise ValueValidationError("amount must be positive")


class IncompleteValue(ValueObjectInterface):
    @property
    def state(self) -> Mapping[str, Any]:
        return {}

    def replace(self, **changes: Any) -> Self:
        return self


def test_equal_state_is_equal_for_distinct_instances():
    first = StateValueObject({"name": "sample", "values": [1, 2]})
    second = StateValueObject({"name": "sample", "values": [1, 2]})

    assert first == second
    assert first is not second


def test_different_state_is_not_equal():
    first = StateValueObject({"name": "first"})
    second = StateValueObject({"name": "second"})

    assert first != second


def test_replace_returns_new_value_without_mutating_original():
    original = StateValueObject({"name": "before", "count": 1})

    replacement = original.replace(name="after")

    assert original.state == {"name": "before", "count": 1}
    assert replacement.state == {"name": "after", "count": 1}
    assert replacement is not original


def test_state_is_defensively_copied():
    original = StateValueObject({"values": [1, 2]})
    exposed_state = original.state
    exposed_state["values"].append(3)

    assert original.state == {"values": [1, 2]}


def test_invalid_field_name_is_rejected():
    with pytest.raises(ValueError, match="field names"):
        StateValueObject({"": 1})


def test_subclass_validation_is_applied_on_construction_and_replacement():
    value = PositiveValue({"amount": 2})

    with pytest.raises(ValueValidationError, match="positive"):
        value.replace(amount=0)


def test_hashing_supports_hashable_state():
    first = StateValueObject({"name": "sample", "count": 1})
    second = StateValueObject({"name": "sample", "count": 1})

    assert hash(first) == hash(second)


def test_hashing_rejects_unhashable_state():
    value = StateValueObject({"values": [1, 2]})

    with pytest.raises(TypeError, match="unhashable"):
        hash(value)


def test_value_object_conforms_to_protocol():
    value = StateValueObject({"name": "sample"})

    assert isinstance(value, ValueSemantics)


def test_interface_and_stateful_implementation_are_separated():
    assert not hasattr(ValueObjectInterface, "_state")

    value = StateValueObject({"name": "sample"})

    assert value.state == {"name": "sample"}
    assert isinstance(value, ValueSemantics)


def test_state_value_object_variants_directly_implement_interface():
    assert getmro(StateValueObjectImmutable)[1] is ValueObjectInterface
    assert getmro(StateValueObjectMutable)[1] is ValueObjectInterface


def test_interface_requires_equality_and_representation_implementations():
    with pytest.raises(TypeError, match="abstract"):
        IncompleteValue()


def test_state_value_object_immutable_is_explicit_template():
    value = StateValueObjectImmutable({"name": "sample"})

    assert value.replace(name="updated") != value


def test_state_value_object_immutable_is_immutable_template():
    value = StateValueObjectImmutable({"name": "sample"})

    assert value.replace(name="updated") != value
    assert not hasattr(value, "update")


def test_state_value_object_mutable_updates_state():
    value = StateValueObjectMutable({"name": "before", "count": 1})

    value.update(name="after")

    assert value.state == {"name": "after", "count": 1}


def test_state_value_object_mutable_update_is_atomic_when_validation_fails():
    value = PositiveValue({"amount": 2})

    with pytest.raises(ValueValidationError, match="positive"):
        value.update(amount=0)

    assert value.state == {"amount": 2}


def test_state_value_object_mutable_is_not_hashable():
    with pytest.raises(TypeError):
        hash(StateValueObjectMutable({"name": "sample"}))
