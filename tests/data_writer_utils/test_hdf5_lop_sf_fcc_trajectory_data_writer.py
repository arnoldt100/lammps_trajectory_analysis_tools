from pathlib import Path
from typing import Any, Callable

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    SPATIAL_DIMENSION,
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
)

DATASET_NAMES = ("positions", "lop_sf_fcc", "box_lengths", "box_angles", "step_number")
FrameFactory = Callable[..., dict[str, Any]]
WriteFrames = Callable[..., None]


def test_configuration_reports_the_target_layout_and_metadata(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    configuration = writer.configuration

    assert configuration["file_path"] == file_path
    assert configuration["number_of_trajectories"] == metadata.number_of_trajectories
    assert configuration["number_of_atoms"] == layout.number_of_atoms
    assert configuration["spatial_dimension"] == SPATIAL_DIMENSION
    assert configuration["dataset_dtypes"] == layout.dataset_dtypes
    assert configuration["chunk_shapes"] == layout.chunk_shapes
    assert configuration["metadata"] == metadata.as_attributes()


def test_constructor_rejects_invalid_configuration(
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        HDF5LopSfFccTrajectoryDataWriter(
            file_path, metadata.replace({"time_units": 0.0}), layout
        )
    with pytest.raises(DataWriterConfigurationError):
        HDF5LopSfFccTrajectoryDataWriter(
            file_path, metadata, layout.replace({"number_of_atoms": 0})
        )


def test_create_writes_root_metadata_and_every_trajectory_group(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
) -> None:
    writer.create()
    writer.close()

    with h5py.File(file_path, "r") as output:
        assert output.attrs["generating_machine"] == metadata.generating_machine
        assert output.attrs["time_units"] == pytest.approx(metadata.time_units)
        names = sorted(output["trajectories"].keys())
        assert names == [
            f"traj_{index:05d}" for index in range(metadata.number_of_trajectories)
        ]


def test_pre_created_groups_hold_every_empty_dataset(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    file_path: Path,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    writer.create()
    writer.close()

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00000"]
        assert group.attrs["trajectory_index"] == 0
        assert sorted(group.keys()) == sorted(DATASET_NAMES)
        for name in DATASET_NAMES:
            dataset = group[name]
            frame_shape = layout.frame_shapes[name]
            assert dataset.shape == (0, *frame_shape)
            assert dataset.maxshape == (None, *frame_shape)
            assert dataset.chunks == layout.chunk_shapes[name]
            assert dataset.dtype == np.dtype(layout.dataset_dtypes[name])
        assert group["box_lengths"].attrs["units"] == layout.length_units_label
        assert group["box_angles"].attrs["units"] == "degrees"


def test_create_refuses_to_overwrite_an_existing_target(
    writer: HDF5LopSfFccTrajectoryDataWriter, file_path: Path
) -> None:
    file_path.write_bytes(b"existing contents")
    original = file_path.read_bytes()

    with pytest.raises(DataWriterTargetError):
        writer.create()

    assert file_path.read_bytes() == original


def test_append_accepts_a_single_frame_and_a_batch_in_order(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
) -> None:
    first = make_frames(frame_count=1, first_step=0)
    rest = make_frames(frame_count=2, first_step=10, offset=100.0)

    write_frames(created_writer, "append_trajectory_frames", 0, first)
    write_frames(created_writer, "append_trajectory_frames", 0, rest)
    created_writer.close()

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00000"]
        assert group["step_number"].shape == (3,)
        np.testing.assert_array_equal(group["step_number"][...], [0, 10, 20])
        for name in DATASET_NAMES:
            assert group[name].shape[0] == 3
        np.testing.assert_allclose(
            group["positions"][1:],
            rest["positions"].astype(np.float32),
        )


def test_appends_to_different_trajectories_stay_independent(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
) -> None:
    write_frames(created_writer, "append_trajectory_frames", 0, make_frames(2))
    write_frames(created_writer, "append_trajectory_frames", 2, make_frames(1))
    created_writer.close()

    with h5py.File(file_path, "r") as output:
        trajectories = output["trajectories"]
        assert trajectories["traj_00000"]["step_number"].shape == (2,)
        assert trajectories["traj_00001"]["step_number"].shape == (0,)
        assert trajectories["traj_00002"]["step_number"].shape == (1,)


def test_write_trajectory_replaces_rather_than_appends(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
) -> None:
    write_frames(created_writer, "write_trajectory", 0, make_frames(3))
    replacement = make_frames(frame_count=1, first_step=50, offset=7.0)
    write_frames(created_writer, "write_trajectory", 0, replacement)
    created_writer.close()

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00000"]
        assert group["step_number"].shape == (1,)
        np.testing.assert_array_equal(group["step_number"][...], [50])


def test_values_round_trip_exactly_for_float64_storage(
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
) -> None:
    precise = layout.replace(
        {"position_dtype": "float64", "lop_sf_fcc_dtype": "float64"}
    )
    frames = make_frames(2)

    with HDF5LopSfFccTrajectoryDataWriter(file_path, metadata, precise) as writer:
        write_frames(writer, "append_trajectory_frames", 0, frames)

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00000"]
        np.testing.assert_array_equal(group["positions"][...], frames["positions"])
        np.testing.assert_array_equal(group["lop_sf_fcc"][...], frames["lop_sf_fcc"])


def test_values_round_trip_within_tolerance_for_float32_storage(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
) -> None:
    frames = make_frames(2)
    write_frames(created_writer, "append_trajectory_frames", 0, frames)
    created_writer.close()

    with h5py.File(file_path, "r") as output:
        group = output["trajectories"]["traj_00000"]
        np.testing.assert_allclose(
            group["positions"][...], frames["positions"], rtol=1e-6
        )


def test_writing_before_create_raises_a_lifecycle_error(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
) -> None:
    with pytest.raises(DataWriterLifecycleError):
        write_frames(writer, "append_trajectory_frames", 0, make_frames(1))


def test_writing_after_close_raises_a_lifecycle_error(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
) -> None:
    writer.create()
    writer.close()

    with pytest.raises(DataWriterLifecycleError):
        write_frames(writer, "append_trajectory_frames", 0, make_frames(1))


@pytest.mark.parametrize("trajectory_index", [-1, 3, 99])
def test_out_of_range_trajectory_index_raises_and_creates_no_group(
    created_writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
    trajectory_index: int,
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        write_frames(
            created_writer, "append_trajectory_frames", trajectory_index, make_frames(1)
        )

    created_writer.close()
    with h5py.File(file_path, "r") as output:
        assert len(output["trajectories"]) == 3


def test_close_is_idempotent_and_safe_before_create(
    writer: HDF5LopSfFccTrajectoryDataWriter,
) -> None:
    writer.close()
    writer.create()
    writer.close()
    writer.close()


def test_context_manager_creates_on_entry_and_closes_on_exit(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    make_frames: FrameFactory,
    write_frames: WriteFrames,
    file_path: Path,
) -> None:
    with writer as entered:
        assert entered is writer
        write_frames(entered, "append_trajectory_frames", 1, make_frames(1))

    with pytest.raises(DataWriterLifecycleError):
        write_frames(writer, "append_trajectory_frames", 1, make_frames(1))
    assert file_path.exists()


def test_context_manager_closes_when_the_block_raises(
    writer: HDF5LopSfFccTrajectoryDataWriter,
) -> None:
    with pytest.raises(RuntimeError):
        with writer:
            raise RuntimeError("failure inside the context")

    with pytest.raises(DataWriterLifecycleError):
        writer._require_group(0)


def test_trajectories_without_data_remain_readable_empty_datasets(
    created_writer: HDF5LopSfFccTrajectoryDataWriter, file_path: Path
) -> None:
    created_writer.close()

    with h5py.File(file_path, "r") as output:
        for group in output["trajectories"].values():
            for name in DATASET_NAMES:
                assert group[name].shape[0] == 0
