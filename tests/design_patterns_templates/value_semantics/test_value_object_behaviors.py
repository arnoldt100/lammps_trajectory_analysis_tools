"""Tests for the public value_object_behaviors free functions."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics import (
    ConcreteStateImplementation,
    NumericStateImplementation,
    StateValueObjectImmutable,
    StateValueObjectMutable,
    hash_state,
    invoke_dummy_method,
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
        updated_state = dict(state)
        updated_state.update(changes)
        return updated_state

    def update_state(self, state: Any, changes: Any) -> Any:
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


def test_hash_state_matches_for_equal_mapping_state():
    first = StateValueObjectImmutable({"name": "sample", "count": 1}, BEHAVIOR)
    second = StateValueObjectImmutable({"name": "sample", "count": 1}, BEHAVIOR)

    assert hash_state(first) == hash_state(second)


def test_hash_state_differs_for_different_mapping_state():
    first = StateValueObjectImmutable({"name": "first"}, BEHAVIOR)
    second = StateValueObjectImmutable({"name": "second"}, BEHAVIOR)

    assert hash_state(first) != hash_state(second)


def test_hash_state_supports_owned_object_state():
    value = StateValueObjectMutable(NumericStateImplementation(42), BEHAVIOR)

    assert isinstance(hash_state(value), int)


def test_invoke_dummy_method_delegates_to_owned_object(
    capsys: pytest.CaptureFixture[str],
) -> None:
    value = StateValueObjectMutable(ConcreteStateImplementation("owned message"), BEHAVIOR)

    invoke_dummy_method(value)

    assert capsys.readouterr().out == "owned message\n"


def test_invoke_dummy_method_works_for_immutable_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    value = StateValueObjectImmutable(ConcreteStateImplementation("immutable message"), BEHAVIOR)

    invoke_dummy_method(value)

    assert capsys.readouterr().out == "immutable message\n"
