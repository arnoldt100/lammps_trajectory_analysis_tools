from pathlib import Path
from typing import Callable

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object import (
    HDF5LopSfFccTrajectoryWriterValueObject,
)

APPEND = "append_trajectory_frames"


def test_open_for_append_keeps_stored_frames_and_appends_after_them(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    make_frames: Callable,
    write_frames: Callable,
) -> None:
    first = make_frames(frame_count=2, first_step=0)
    second = make_frames(frame_count=3, first_step=20, offset=100.0)
    writer.create()
    write_frames(writer, APPEND, 1, first)
    writer.close()

    writer.open_for_append()
    write_frames(writer, APPEND, 1, second)
    writer.close()

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00001"]
        np.testing.assert_array_equal(
            group["step_number"][...],
            np.concatenate([first["step_number"], second["step_number"]]),
        )
        np.testing.assert_allclose(
            group["lop_sf_fcc"][...],
            np.concatenate([first["lop_sf_fcc"], second["lop_sf_fcc"]]),
        )


def test_open_for_append_preserves_root_metadata(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
) -> None:
    writer.create()
    writer.close()
    writer.open_for_append()
    writer.close()

    with h5py.File(file_path, "r") as output:
        assert output.attrs["generating_machine"] == metadata.generating_machine


def test_open_for_append_still_requires_increasing_steps(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: Callable,
    write_frames: Callable,
) -> None:
    writer.create()
    write_frames(writer, APPEND, 0, make_frames(frame_count=2, first_step=0))
    writer.close()

    writer.open_for_append()
    with pytest.raises(DataWriterConfigurationError):
        write_frames(writer, APPEND, 0, make_frames(frame_count=1, first_step=10))
    writer.close()


def test_open_for_append_rejects_missing_target(
    writer: HDF5LopSfFccTrajectoryDataWriter,
) -> None:
    with pytest.raises(DataWriterTargetError):
        writer.open_for_append()


def test_open_for_append_rejects_mismatched_trajectory_count(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    writer.create()
    writer.close()
    other = HDF5LopSfFccTrajectoryDataWriter(
        file_path,
        metadata.replace({"number_of_trajectories": metadata.number_of_trajectories + 1}),
        layout,
    )
    with pytest.raises(DataWriterConfigurationError):
        other.open_for_append()


def test_open_for_append_rejects_mismatched_atom_count(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    writer.create()
    writer.close()
    other = HDF5LopSfFccTrajectoryDataWriter(
        file_path,
        metadata,
        layout.replace({"number_of_atoms": layout.number_of_atoms + 1}),
    )
    with pytest.raises(DataWriterConfigurationError):
        other.open_for_append()


def test_value_object_appends_across_contexts(
    value_object: HDF5LopSfFccTrajectoryWriterValueObject,
    file_path: Path,
    make_frames: Callable,
    write_frames: Callable,
) -> None:
    first = make_frames(frame_count=2, first_step=0)
    second = make_frames(frame_count=2, first_step=20)

    with value_object as writer:
        write_frames(writer, APPEND, 2, first)
    with value_object.open_for_append() as writer:
        write_frames(writer, APPEND, 2, second)

    with h5py.File(file_path, "r") as output:
        assert output["trajectories"]["traj_00002"]["step_number"].shape == (4,)
