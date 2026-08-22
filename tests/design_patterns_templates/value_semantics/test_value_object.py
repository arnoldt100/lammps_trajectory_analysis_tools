from collections.abc import Mapping
from copy import deepcopy
from inspect import getmro
from typing import Any, Self

import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics import (
    ConcreteStateImplementation,
    NumericStateImplementation,
    StateValueObjectImmutable,
    StateValueObjectMutable,
    ValueObjectInterface,
    ValueSemantics,
    ValueValidationError,
)


class DefaultStateBehavior:
    """Test-only default behavior implementing ``StateValueBehaviorProtocol``."""

    def copy_state(self, state: Any) -> Any:
        return deepcopy(state)

    def validate_state(self, state: Any) -> None:
        validator = getattr(state, "validate_state", None)
        if validator is not None:
            validator()
            return
        if isinstance(state, Mapping) and any(
            not isinstance(name, str) or not name for name in state
        ):
            raise ValueError("state field names must be non-empty strings")

    def replace_state(self, state: Any, changes: Any) -> Any:
        replacer = getattr(state, "replace", None)
        if replacer is not None:
            return replacer(changes)
        if not isinstance(state, Mapping) or not isinstance(changes, Mapping):
            raise TypeError("default behavior requires mapping state and changes")
        updated_state = dict(state)
        updated_state.update(changes)
        return updated_state

    def update_state(self, state: Any, changes: Any) -> Any:
        updater = getattr(state, "update", None)
        if updater is not None and not isinstance(state, Mapping):
            updated_state = self.copy_state(state)
            updated_state.update(changes)
            return updated_state
        return self.replace_state(state, changes)

    def states_equal(self, left: Any, right: Any) -> bool:
        return left == right

    def state_repr(self, state: Any) -> str:
        return repr(state)

    def hash_state(self, state: Any) -> int:
        if isinstance(state, dict):
            return hash(tuple(sorted(state.items())))
        return hash(state)

    def dummy_method(self, owned_object: Any, *args: Any, **kwargs: Any) -> Any:
        return owned_object.dummy_method(*args, **kwargs)


BEHAVIOR = DefaultStateBehavior()


class PositiveBehavior(DefaultStateBehavior):
    def validate_state(self, state: Any) -> None:
        if state.get("amount", 0) <= 0:
            raise ValueValidationError("amount must be positive")


class IncompleteValue(ValueObjectInterface):
    @property
    def state(self) -> Mapping[str, Any]:
        return {}

    def replace(self, **changes: Any) -> Self:
        return self


def test_equal_state_is_equal_for_distinct_instances():
    first = StateValueObjectImmutable({"name": "sample", "values": [1, 2]}, BEHAVIOR)
    second = StateValueObjectImmutable({"name": "sample", "values": [1, 2]}, BEHAVIOR)

    assert first == second
    assert first is not second


def test_different_state_is_not_equal():
    first = StateValueObjectImmutable({"name": "first"}, BEHAVIOR)
    second = StateValueObjectImmutable({"name": "second"}, BEHAVIOR)

    assert first != second


def test_replace_returns_new_value_without_mutating_original():
    original = StateValueObjectImmutable({"name": "before", "count": 1}, BEHAVIOR)

    replacement = original.replace({"name": "after"})

    assert original.state == {"name": "before", "count": 1}
    assert replacement.state == {"name": "after", "count": 1}
    assert replacement is not original


def test_state_is_defensively_copied():
    original = StateValueObjectImmutable({"values": [1, 2]}, BEHAVIOR)
    exposed_state = original.state
    exposed_state["values"].append(3)

    assert original.state == {"values": [1, 2]}


def test_invalid_field_name_is_rejected():
    with pytest.raises(ValueError, match="field names"):
        StateValueObjectImmutable({"": 1}, BEHAVIOR)


def test_behavior_validation_is_applied_on_construction_and_replacement():
    value = StateValueObjectMutable({"amount": 2}, PositiveBehavior())

    with pytest.raises(ValueValidationError, match="positive"):
        value.replace({"amount": 0})


def test_hashing_supports_hashable_state():
    first = StateValueObjectImmutable({"name": "sample", "count": 1}, BEHAVIOR)
    second = StateValueObjectImmutable({"name": "sample", "count": 1}, BEHAVIOR)

    assert hash(first) == hash(second)


def test_hashing_rejects_unhashable_state():
    value = StateValueObjectImmutable({"values": [1, 2]}, BEHAVIOR)

    with pytest.raises(TypeError, match="unhashable"):
        hash(value)


def test_value_object_conforms_to_protocol():
    value = StateValueObjectImmutable({"name": "sample"}, BEHAVIOR)

    assert isinstance(value, ValueSemantics)


def test_interface_and_stateful_implementation_are_separated():
    assert not hasattr(ValueObjectInterface, "_state")

    value = StateValueObjectImmutable({"name": "sample"}, BEHAVIOR)

    assert value.state == {"name": "sample"}
    assert isinstance(value, ValueSemantics)


def test_state_value_object_variants_directly_implement_interface():
    assert getmro(StateValueObjectImmutable)[1] is ValueObjectInterface
    assert getmro(StateValueObjectMutable)[1] is ValueObjectInterface


def test_interface_requires_equality_and_representation_implementations():
    with pytest.raises(TypeError, match="abstract"):
        IncompleteValue()


def test_state_value_object_immutable_is_explicit_template():
    value = StateValueObjectImmutable({"name": "sample"}, BEHAVIOR)

    assert value.replace({"name": "updated"}) != value


def test_state_value_object_immutable_is_immutable_template():
    value = StateValueObjectImmutable({"name": "sample"}, BEHAVIOR)

    assert value.replace({"name": "updated"}) != value
    assert not hasattr(value, "update")


def test_state_value_object_mutable_updates_state():
    value = StateValueObjectMutable({"name": "before", "count": 1}, BEHAVIOR)

    value.update({"name": "after"})

    assert value.state == {"name": "after", "count": 1}


def test_state_value_object_mutable_update_is_atomic_when_validation_fails():
    value = StateValueObjectMutable({"amount": 2}, PositiveBehavior())

    with pytest.raises(ValueValidationError, match="positive"):
        value.update({"amount": 0})

    assert value.state == {"amount": 2}


def test_state_value_object_mutable_is_not_hashable():
    with pytest.raises(TypeError):
        hash(StateValueObjectMutable({"name": "sample"}, BEHAVIOR))


def test_placeholder_behavior_is_shared_by_value_object_templates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[dict[str, Any], tuple[Any, ...], dict[str, Any]]] = []

    def shared_dummy_method(
        behavior: DefaultStateBehavior,
        owned_object: Any,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        calls.append((owned_object, args, kwargs))
        return "handled"

    monkeypatch.setattr(DefaultStateBehavior, "dummy_method", shared_dummy_method)

    mutable_value = StateValueObjectMutable({"name": "mutable"}, BEHAVIOR)
    immutable_value = StateValueObjectImmutable({"name": "immutable"}, BEHAVIOR)

    assert mutable_value.dummy_method(1, mode="mutable") == "handled"
    assert immutable_value.dummy_method(2, mode="immutable") == "handled"
    assert calls == [
        ({"name": "mutable"}, (1,), {"mode": "mutable"}),
        ({"name": "immutable"}, (2,), {"mode": "immutable"}),
    ]


def test_value_object_supports_non_mapping_state_with_custom_behavior() -> None:
    class IntegerBehavior(DefaultStateBehavior):
        def replace_state(self, state: Any, changes: Any) -> int:
            return state + changes

        def update_state(self, state: Any, changes: Any) -> int:
            return state + changes

    behavior = IntegerBehavior()
    immutable_value = StateValueObjectImmutable(10, behavior)
    mutable_value = StateValueObjectMutable(10, behavior)

    assert immutable_value.replace(2).state == 12
    mutable_value.update(3)
    assert mutable_value.state == 13


def test_concrete_state_implementation_is_an_independent_owned_object(
    capsys: pytest.CaptureFixture[str],
) -> None:
    owned_object = ConcreteStateImplementation("sample message")

    assert owned_object.message == "sample message"
    assert not isinstance(owned_object, StateValueObjectMutable)
    assert not isinstance(owned_object, StateValueObjectImmutable)

    owned_object.validate_state()

    owned_object.dummy_method()

    assert capsys.readouterr().out == "sample message\n"


def test_value_object_delegates_dummy_method_to_owned_object(
    capsys: pytest.CaptureFixture[str],
) -> None:
    owned_object = ConcreteStateImplementation("owned message")
    value = StateValueObjectMutable(owned_object, BEHAVIOR)

    value.dummy_method()

    assert capsys.readouterr().out == "owned message\n"


def test_immutable_value_object_delegates_dummy_method_to_owned_object(
    capsys: pytest.CaptureFixture[str],
) -> None:
    owned_object = ConcreteStateImplementation("immutable message")
    value = StateValueObjectImmutable(owned_object, BEHAVIOR)

    value.dummy_method()

    assert capsys.readouterr().out == "immutable message\n"


@pytest.mark.parametrize(
    ("wrapper_type", "expected_output"),
    [
        (StateValueObjectMutable, "42\n"),
        (StateValueObjectImmutable, "42\n"),
    ],
)
def test_shared_behavior_supports_a_second_owned_object_type(
    wrapper_type: type[StateValueObjectMutable | StateValueObjectImmutable],
    expected_output: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    value = wrapper_type(NumericStateImplementation(42), BEHAVIOR)

    value.dummy_method()

    assert capsys.readouterr().out == expected_output


def test_owned_objects_validate_their_own_state() -> None:
    with pytest.raises(ValueError, match="message"):
        ConcreteStateImplementation("").validate_state()

    NumericStateImplementation(42).validate_state()


def test_owned_objects_understand_their_change_representation() -> None:
    mutable_value = StateValueObjectMutable(
        NumericStateImplementation(42),
        BEHAVIOR,
    )
    immutable_value = StateValueObjectImmutable(
        NumericStateImplementation(42),
        BEHAVIOR,
    )

    replacement = immutable_value.replace(43)
    mutable_value.update(43)

    assert replacement.state.value == 43
    assert mutable_value.state.value == 43
