"""Tests for the VTKHDF animation writer value object."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.protocols import (
    ValueSemantics,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object import (
    LopSfFccVtkhdfAnimationWriterValueObject,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_interface import (
    LopSfFccVtkhdfAnimationWriterValueObjectInterface,
)


def _append(value_object: LopSfFccVtkhdfAnimationWriterValueObject) -> None:
    value_object.append_frames(
        np.asarray([0], dtype=np.int64),
        np.zeros((1, 4, 3)),
        np.zeros((1, 4)),
        np.asarray([[10.0, 10.0, 10.0]]),
        np.asarray([[90.0, 90.0, 90.0]]),
    )


def test_value_object_satisfies_both_contracts(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    assert isinstance(
        value_object,
        LopSfFccVtkhdfAnimationWriterValueObjectInterface,
    )
    assert isinstance(value_object, ValueSemantics)


def test_constructor_validates_state(
    state: LopSfFccVtkhdfAnimationWriterState,
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    writer_builder: Callable[[LopSfFccVtkhdfAnimationWriterState], Any],
) -> None:
    invalid = state.replace({"file_path": Path("invalid.h5")})

    with pytest.raises(DataWriterConfigurationError):
        LopSfFccVtkhdfAnimationWriterValueObject(invalid, behavior, writer_builder)


def test_state_accessors_drop_the_writer_resource(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    value_object.create()

    assert value_object.state.writer is None
    assert value_object.state_implementations.writer is None
    assert value_object.writer_configuration["created"] is True


def test_metadata_is_defensive(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    metadata = value_object.metadata
    metadata["compiler_build_flags"].append("-g")

    assert value_object.metadata["compiler_build_flags"] == [
        "-O3",
        "-march=native",
    ]


def test_equal_values_ignore_attached_writer_resources(
    state: LopSfFccVtkhdfAnimationWriterState,
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    writer_builder: Callable[[LopSfFccVtkhdfAnimationWriterState], Any],
) -> None:
    first = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior, writer_builder)
    second = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior, writer_builder)

    first.create()

    assert first == second
    assert first.__eq__(object()) is NotImplemented


def test_replace_is_independent_handle_free_and_validated(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
    tmp_path: Path,
) -> None:
    value_object.create()
    replacement_path = tmp_path / "replacement.vtkhdf"

    replacement = value_object.replace({"file_path": replacement_path})

    assert replacement.state.file_path == replacement_path
    assert replacement.state.writer is None
    assert value_object.writer_configuration["created"] is True
    with pytest.raises(DataWriterLifecycleError):
        _ = replacement.writer_configuration
    with pytest.raises(DataWriterConfigurationError):
        value_object.replace({"file_path": tmp_path / "invalid.h5"})


def test_update_is_validated_and_blocked_while_open(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    changed_layout = value_object.state.layout.replace({"number_of_atoms": 8})
    value_object.update({"layout": changed_layout})
    assert value_object.state.layout.number_of_atoms == 8

    previous = value_object.state
    with pytest.raises(DataWriterConfigurationError):
        value_object.update({"layout": previous.layout.replace({"number_of_atoms": 0})})
    assert value_object.state == previous

    value_object.create()
    with pytest.raises(DataWriterLifecycleError):
        value_object.update({"layout": previous.layout})


def test_writer_operations_require_an_attached_writer(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    with pytest.raises(DataWriterLifecycleError):
        _ = value_object.writer_configuration
    with pytest.raises(DataWriterLifecycleError):
        _append(value_object)


def test_create_append_close_and_open_for_append_delegate_lifecycle(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    value_object.create()
    _append(value_object)
    assert value_object.writer_configuration["append_count"] == 1
    value_object.close()
    with pytest.raises(DataWriterLifecycleError):
        _ = value_object.writer_configuration

    returned = value_object.open_for_append()
    assert returned is value_object
    assert value_object.writer_configuration["opened_for_append"] is True


def test_context_success_closes_and_exception_aborts(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    with value_object:
        _append(value_object)
    with pytest.raises(DataWriterLifecycleError):
        _ = value_object.writer_configuration

    with pytest.raises(RuntimeError, match="stop"), value_object:
        raise RuntimeError("stop")
    with pytest.raises(DataWriterLifecycleError):
        _ = value_object.writer_configuration


def test_repr_and_hash_policy_exclude_the_writer(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    value_object.create()

    assert "StubWriterProduct" not in repr(value_object)
    assert type(value_object).__hash__ is None
    with pytest.raises(TypeError):
        hash(value_object)


def test_dummy_method_returns_the_template_placeholder(
    value_object: LopSfFccVtkhdfAnimationWriterValueObject,
) -> None:
    assert value_object.dummy_method() is None


def test_shared_behavior_does_not_mix_construction_dependencies(
    state: LopSfFccVtkhdfAnimationWriterState,
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    writer_builder: Callable[[LopSfFccVtkhdfAnimationWriterState], Any],
    tmp_path: Path,
) -> None:
    first_states: list[LopSfFccVtkhdfAnimationWriterState] = []
    second_states: list[LopSfFccVtkhdfAnimationWriterState] = []

    def first_builder(current: LopSfFccVtkhdfAnimationWriterState) -> Any:
        first_states.append(current)
        return writer_builder(current)

    def second_builder(current: LopSfFccVtkhdfAnimationWriterState) -> Any:
        second_states.append(current)
        return writer_builder(current)

    first = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior, first_builder)
    second_state = state.replace({"file_path": tmp_path / "second.vtkhdf"})
    second = LopSfFccVtkhdfAnimationWriterValueObject(
        second_state, behavior, second_builder
    )
    try:
        first.create()
        second.open_for_append()
        assert first_states == [state]
        assert second_states == [second_state]
        assert first.writer_configuration["file_path"] == state.file_path
        assert second.writer_configuration["file_path"] == second_state.file_path
    finally:
        first.abort()
        second.abort()


@pytest.mark.parametrize("operation", ["create", "open_for_append"])
def test_construction_failure_leaves_the_value_closed_and_retryable(
    state: LopSfFccVtkhdfAnimationWriterState,
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    writer_builder: Callable[[LopSfFccVtkhdfAnimationWriterState], Any],
    operation: str,
) -> None:
    calls = 0

    def build(current: LopSfFccVtkhdfAnimationWriterState) -> Any:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("construction failed")
        return writer_builder(current)

    value = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior, build)
    with pytest.raises(RuntimeError, match="construction failed"):
        getattr(value, operation)()
    assert value.state == state
    with pytest.raises(DataWriterLifecycleError):
        _ = value.writer_configuration
    try:
        getattr(value, operation)()
        assert calls == 2
        assert value.writer_configuration["file_path"] == state.file_path
    finally:
        value.abort()


@pytest.mark.parametrize("operation", ["create", "open_for_append"])
def test_lifecycle_failure_does_not_attach_the_supplied_writer(
    state: LopSfFccVtkhdfAnimationWriterState,
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    stub_writer: Any,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    def fail() -> None:
        raise RuntimeError("lifecycle failed")

    monkeypatch.setattr(stub_writer, operation, fail)
    value = LopSfFccVtkhdfAnimationWriterValueObject(
        state, behavior, lambda current: stub_writer
    )
    with pytest.raises(RuntimeError, match="lifecycle failed"):
        getattr(value, operation)()
    assert value.state == state
    with pytest.raises(DataWriterLifecycleError):
        _ = value.writer_configuration
