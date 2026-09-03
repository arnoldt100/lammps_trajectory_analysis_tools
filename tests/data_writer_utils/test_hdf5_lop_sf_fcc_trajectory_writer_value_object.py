from pathlib import Path
from typing import Any, Callable

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_behavior import (
    LopSfFccTrajectoryWriterBehavior,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object import (
    HDF5LopSfFccTrajectoryWriterValueObject,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object_interface import (
    LopSfFccTrajectoryWriterValueObjectInterface,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.protocols import (
    ValueSemantics,
)

FrameFactory = Callable[..., dict[str, Any]]


def append(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
    trajectory_index: int,
    frames: dict[str, Any],
) -> None:
    value_object.append_trajectory_frames(
        trajectory_index,
        frames["step_number"],
        frames["positions"],
        frames["lop_sf_fcc"],
        frames["box_lengths"],
        frames["box_angles"],
    )


def test_value_object_satisfies_its_interface_and_value_semantics(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    assert isinstance(value_object, LopSfFccTrajectoryWriterValueObjectInterface)
    assert isinstance(value_object, ValueSemantics)


def test_constructor_validates_the_incoming_state(
    state: LopSfFccTrajectoryWriterState,
    behavior: LopSfFccTrajectoryWriterBehavior,
) -> None:
    invalid = state.replace({"layout": state.layout.replace({"number_of_atoms": 0})})

    with pytest.raises(DataWriterConfigurationError):
        HDF5LopSfFccTrajectoryWriterValueObject(invalid, behavior)


def test_state_accessors_return_defensive_copies(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    value_object.create()

    assert value_object.state_implementations.writer is None
    assert value_object.state.writer is None
    assert value_object.writer_configuration is not None


def test_metadata_returns_a_copy_that_cannot_affect_the_object(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    metadata = value_object.metadata
    metadata["generating_machine"] = "mutated"

    assert value_object.metadata["generating_machine"] != "mutated"


def test_equal_arguments_produce_equal_objects_before_and_after_create(
    state: LopSfFccTrajectoryWriterState,
    behavior: LopSfFccTrajectoryWriterBehavior,
) -> None:
    first = HDF5LopSfFccTrajectoryWriterValueObject(state, behavior)
    second = HDF5LopSfFccTrajectoryWriterValueObject(state, behavior)

    assert first == second
    first.create()
    try:
        assert first == second
    finally:
        first.close()


def test_replace_returns_a_handle_free_object_and_leaves_the_original_open(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject, tmp_path: Path
) -> None:
    value_object.create()
    target = tmp_path / "replaced.h5"

    replaced = value_object.replace({"file_path": target})

    assert replaced.state.file_path == target
    assert value_object.state.file_path != target
    with pytest.raises(DataWriterLifecycleError):
        replaced.writer_configuration
    assert value_object.writer_configuration["file_path"] != target


def test_update_succeeds_before_create(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    changed = value_object.state.layout.replace({"number_of_atoms": 6})

    value_object.update({"layout": changed})

    assert value_object.state.layout.number_of_atoms == 6


def test_update_is_blocked_while_the_writer_is_open(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject, tmp_path: Path
) -> None:
    value_object.create()
    original = value_object.state

    with pytest.raises(DataWriterLifecycleError):
        value_object.update({"file_path": tmp_path / "other.h5"})

    assert value_object.state == original


def test_update_with_invalid_changes_leaves_the_previous_state(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    original = value_object.state

    with pytest.raises(DataWriterConfigurationError):
        value_object.update(
            {"layout": value_object.state.layout.replace({"number_of_atoms": 0})}
        )

    assert value_object.state == original


def test_value_object_is_unhashable(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    assert type(value_object).__hash__ is None
    with pytest.raises(TypeError):
        hash(value_object)


def test_writer_operations_before_create_raise_a_lifecycle_error(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
    make_frames: FrameFactory,
) -> None:
    with pytest.raises(DataWriterLifecycleError):
        value_object.writer_configuration
    with pytest.raises(DataWriterLifecycleError):
        append(value_object, 0, make_frames(1))


def test_close_releases_the_handle_and_leaves_the_object_inspectable(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    value_object.create()

    value_object.close()

    assert value_object.state.writer is None
    assert value_object.metadata["generating_machine"] == "nimzoindian"
    value_object.close()


def test_context_manager_creates_appends_and_closes(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
    make_frames: FrameFactory,
    file_path: Path,
) -> None:
    with value_object as entered:
        append(entered, 1, make_frames(2))

    with pytest.raises(DataWriterLifecycleError):
        append(value_object, 1, make_frames(1))

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00001"]
        np.testing.assert_array_equal(group["step_number"][...], [0, 10])


def test_repr_omits_the_owned_writer(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    value_object.create()

    assert "HDF5LopSfFccTrajectoryDataWriter" not in repr(value_object)


def test_dummy_method_returns_the_template_placeholder(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    assert value_object.dummy_method() is None


def test_comparison_with_another_type_is_not_implemented(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
) -> None:
    assert value_object.__eq__(object()) is NotImplemented
