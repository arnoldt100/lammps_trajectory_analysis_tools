"""Tests for the VTKHDF animation writer value object."""

from pathlib import Path

import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.protocols import (
    ValueSemantics,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object import (
    LopSfFccVtkhdfAnimationWriterValueObject,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_interface import (
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
) -> None:
    invalid = state.replace({"file_path": Path("invalid.h5")})

    with pytest.raises(DataWriterConfigurationError):
        LopSfFccVtkhdfAnimationWriterValueObject(invalid, behavior)


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
) -> None:
    first = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior)
    second = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior)

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
