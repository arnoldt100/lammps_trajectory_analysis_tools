from pathlib import Path
from typing import Any, Callable

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)

FrameFactory = Callable[..., dict[str, Any]]
WriteFrames = Callable[..., None]
WRITE_METHODS = ["write_trajectory", "append_trajectory_frames"]


@pytest.fixture(params=WRITE_METHODS)
def method_name(request: pytest.FixtureRequest) -> str:
    return request.param


def test_mismatched_frame_counts_are_rejected(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
) -> None:
    frames = make_frames(3)
    frames["box_angles"] = frames["box_angles"][:2]

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, frames)


@pytest.mark.parametrize(
    ("name", "wrong_value"),
    [
        ("positions", np.zeros((2, 4, 2))),
        ("positions", np.zeros((2, 5, 3))),
        ("lop_sf_fcc", np.zeros((2, 5))),
        ("box_lengths", np.ones((2, 2))),
        ("box_angles", np.full((2, 4), 90.0)),
        ("step_number", np.zeros((2, 2), dtype=np.int64)),
    ],
)
def test_wrong_shapes_are_rejected(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
    name: str,
    wrong_value: np.ndarray,
) -> None:
    frames = make_frames(2)
    frames[name] = wrong_value

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, frames)


@pytest.mark.parametrize(
    ("name", "wrong_value"),
    [
        ("positions", np.zeros((2, 4, 3), dtype=np.complex128)),
        ("step_number", np.array([0.5, 1.5])),
    ],
)
def test_uncastable_dtypes_are_rejected(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
    name: str,
    wrong_value: np.ndarray,
) -> None:
    frames = make_frames(2)
    frames[name] = wrong_value

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, frames)


def test_float64_input_is_accepted_by_float32_storage(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
) -> None:
    frames = make_frames(2)

    assert frames["positions"].dtype == np.float64
    write_frames(created_writer, method_name, 0, frames)


@pytest.mark.parametrize(
    "steps",
    [
        np.array([-1, 0], dtype=np.int64),
        np.array([10, 10], dtype=np.int64),
        np.array([20, 10], dtype=np.int64),
    ],
)
def test_invalid_step_numbers_are_rejected(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
    steps: np.ndarray,
) -> None:
    frames = make_frames(2)
    frames["step_number"] = steps

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, frames)


@pytest.mark.parametrize("length", [0.0, -1.0])
def test_non_positive_box_lengths_are_rejected(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
    length: float,
) -> None:
    frames = make_frames(2)
    frames["box_lengths"][1, 0] = length

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, frames)


@pytest.mark.parametrize("angle", [0.0, 180.0, -90.0, 200.0])
def test_out_of_range_lattice_angles_are_rejected(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
    angle: float,
) -> None:
    frames = make_frames(2)
    frames["box_angles"][0, 2] = angle

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, frames)


def test_datasets_are_unchanged_after_a_rejected_call(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
    file_path: Path,
) -> None:
    accepted = make_frames(2)
    write_frames(created_writer, "append_trajectory_frames", 0, accepted)

    rejected = make_frames(frame_count=2, first_step=100, offset=5.0)
    rejected["box_angles"][0, 0] = 0.0
    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, method_name, 0, rejected)

    created_writer.close()
    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00000"]
        assert group["step_number"].shape == (2,)
        np.testing.assert_array_equal(
            group["step_number"][...], accepted["step_number"]
        )
        np.testing.assert_allclose(
            group["positions"][...],
            accepted["positions"].astype(np.float32),
        )


def test_a_single_frame_without_a_leading_axis_matches_the_explicit_form(
    file_path: Path,
    tmp_path: Path,
    metadata,
    layout,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    method_name: str,
) -> None:
    batch = make_frames(1)
    squeezed = {name: values[0] for name, values in batch.items()}
    squeezed["step_number"] = np.int64(batch["step_number"][0])
    other_path = tmp_path / "explicit.h5"

    with HDF5LopSfFccTrajectoryDataWriter(file_path, metadata, layout) as writer:
        write_frames(writer, method_name, 0, squeezed)
    with HDF5LopSfFccTrajectoryDataWriter(other_path, metadata, layout) as writer:
        write_frames(writer, method_name, 0, batch)

    with h5py.File(file_path, "r") as promoted, h5py.File(other_path, "r") as explicit:
        promoted_group = promoted["trajectories"]["traj_00000"]
        explicit_group = explicit["trajectories"]["traj_00000"]
        for name in ("positions", "lop_sf_fcc", "box_lengths", "box_angles", "step_number"):
            np.testing.assert_array_equal(
                promoted_group[name][...], explicit_group[name][...]
            )


def test_append_rejects_steps_that_do_not_follow_the_stored_steps(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
) -> None:
    write_frames(created_writer, "append_trajectory_frames", 0, make_frames(2))
    overlapping = make_frames(frame_count=1, first_step=10)

    with pytest.raises(DataWriterConfigurationError):
        write_frames(created_writer, "append_trajectory_frames", 0, overlapping)

    created_writer.close()
    with h5py.File(file_path, "r") as output:
        assert output["trajectories"]["traj_00000"]["step_number"].shape == (2,)


def test_write_trajectory_may_restart_the_step_sequence(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
) -> None:
    write_frames(created_writer, "write_trajectory", 0, make_frames(2, first_step=100))
    write_frames(created_writer, "write_trajectory", 0, make_frames(2, first_step=0))
