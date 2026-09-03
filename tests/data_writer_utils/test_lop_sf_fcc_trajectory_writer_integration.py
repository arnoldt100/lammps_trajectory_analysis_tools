from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
    data_writer_factory,
)

DATASET_NAMES = ("positions", "lop_sf_fcc", "box_lengths", "box_angles", "step_number")


def build_value_object(
    file_path: Path,
    metadata_arguments: dict,
    layout_arguments: dict,
):
    return data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=metadata_arguments,
        layout=layout_arguments,
    )


@pytest.fixture
def metadata_arguments() -> dict:
    return {
        "time_units": 0.002,
        "time_units_label": "ps",
        "number_of_trajectories": 2,
        "generation_date": datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
        "compiler_build_flags": ("-O3", "-march=native"),
        "generating_machine": "nimzoindian",
        "lmod_modules": ("gcc/13.2.0", "openmpi/4.1.6"),
    }


@pytest.fixture
def layout_arguments() -> dict:
    return {"number_of_atoms": 6, "length_units_label": "angstrom"}


def make_batch(atom_count: int, steps: np.ndarray, seed: int) -> dict:
    generator = np.random.default_rng(seed)
    frame_count = steps.shape[0]
    return {
        "step_number": steps,
        "positions": generator.random((frame_count, atom_count, 3)) * 10.0,
        "lop_sf_fcc": generator.random((frame_count, atom_count)),
        "box_lengths": np.tile([10.0, 11.0, 12.0], (frame_count, 1)),
        "box_angles": np.tile([90.0, 90.0, 90.0], (frame_count, 1)),
    }


def append_batch(value_object, trajectory_index: int, batch: dict) -> None:
    value_object.append_trajectory_frames(
        trajectory_index,
        batch["step_number"],
        batch["positions"],
        batch["lop_sf_fcc"],
        batch["box_lengths"],
        batch["box_angles"],
    )


def test_end_to_end_write_and_read_back(
    tmp_path: Path, metadata_arguments: dict, layout_arguments: dict
) -> None:
    target = tmp_path / "end_to_end.h5"
    atom_count = layout_arguments["number_of_atoms"]
    batches = {
        0: [
            make_batch(atom_count, np.array([0, 10], dtype=np.int64), seed=1),
            make_batch(atom_count, np.array([20], dtype=np.int64), seed=2),
        ],
        1: [make_batch(atom_count, np.array([5, 15, 25], dtype=np.int64), seed=3)],
    }

    value_object = build_value_object(target, metadata_arguments, layout_arguments)
    with value_object as writer:
        for trajectory_index, trajectory_batches in batches.items():
            for batch in trajectory_batches:
                append_batch(writer, trajectory_index, batch)

    with h5py.File(target, "r") as output:
        assert output.attrs["time_units"] == pytest.approx(
            metadata_arguments["time_units"]
        )
        assert output.attrs["generating_machine"] == "nimzoindian"
        np.testing.assert_array_equal(
            output.attrs["lmod_modules"],
            np.array(metadata_arguments["lmod_modules"], dtype=object),
        )
        for trajectory_index, trajectory_batches in batches.items():
            group = output["trajectories"][f"traj_{trajectory_index:05d}"]
            assert group.attrs["trajectory_index"] == trajectory_index
            expected = {
                name: np.concatenate([batch[name] for batch in trajectory_batches])
                for name in DATASET_NAMES
            }
            np.testing.assert_array_equal(
                group["step_number"][...], expected["step_number"]
            )
            np.testing.assert_allclose(
                group["positions"][...],
                expected["positions"].astype(np.float32),
            )
            np.testing.assert_allclose(
                group["lop_sf_fcc"][...],
                expected["lop_sf_fcc"].astype(np.float32),
            )
            np.testing.assert_allclose(
                group["box_lengths"][...], expected["box_lengths"]
            )
            assert group["box_lengths"].attrs["units"] == "angstrom"
            assert group["box_angles"].attrs["units"] == "degrees"


def test_simulation_time_is_derived_from_steps_and_time_units(
    tmp_path: Path, metadata_arguments: dict, layout_arguments: dict
) -> None:
    target = tmp_path / "simulation_time.h5"
    steps = np.array([0, 250, 500], dtype=np.int64)
    batch = make_batch(layout_arguments["number_of_atoms"], steps, seed=4)

    value_object = build_value_object(target, metadata_arguments, layout_arguments)
    with value_object as writer:
        append_batch(writer, 0, batch)

    with h5py.File(target, "r") as output:
        stored_steps = output["trajectories"]["traj_00000"]["step_number"][...]
        simulation_time = stored_steps * output.attrs["time_units"]

    np.testing.assert_allclose(simulation_time, [0.0, 0.5, 1.0])


def test_compressed_and_uncompressed_files_hold_identical_data(
    tmp_path: Path, metadata_arguments: dict, layout_arguments: dict
) -> None:
    plain_path = tmp_path / "plain.h5"
    compressed_path = tmp_path / "compressed.h5"
    steps = np.arange(0, 40, 10, dtype=np.int64)
    batch = make_batch(layout_arguments["number_of_atoms"], steps, seed=5)
    compressed_arguments = {
        **layout_arguments,
        "compression": "gzip",
        "compression_options": 4,
    }

    for path, arguments in ((plain_path, layout_arguments), (compressed_path, compressed_arguments)):
        value_object = build_value_object(path, metadata_arguments, arguments)
        with value_object as writer:
            append_batch(writer, 0, batch)

    with h5py.File(plain_path, "r") as plain, h5py.File(compressed_path, "r") as packed:
        plain_group = plain["trajectories"]["traj_00000"]
        packed_group = packed["trajectories"]["traj_00000"]
        assert plain_group["positions"].compression is None
        assert packed_group["positions"].compression == "gzip"
        for name in DATASET_NAMES:
            np.testing.assert_array_equal(
                plain_group[name][...], packed_group[name][...]
            )


def test_metadata_survives_a_replace_and_a_second_target(
    tmp_path: Path, metadata_arguments: dict, layout_arguments: dict
) -> None:
    first_path = tmp_path / "first.h5"
    second_path = tmp_path / "second.h5"
    value_object = build_value_object(first_path, metadata_arguments, layout_arguments)

    with value_object:
        pass
    replaced = value_object.replace({"file_path": second_path})
    with replaced:
        pass

    assert first_path.exists()
    assert second_path.exists()
    with h5py.File(second_path, "r") as output:
        assert output.attrs["generating_machine"] == "nimzoindian"


def test_a_pre_built_metadata_value_is_reused_across_writers(
    tmp_path: Path, metadata_arguments: dict, layout_arguments: dict
) -> None:
    shared_metadata = LopSfFccRunMetadata(**metadata_arguments)
    shared_layout = LopSfFccTrajectoryLayout(**layout_arguments)

    first = data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=tmp_path / "shared_first.h5",
        metadata=shared_metadata,
        layout=shared_layout,
    )
    second = data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=tmp_path / "shared_second.h5",
        metadata=shared_metadata,
        layout=shared_layout,
    )

    assert first.state.metadata is shared_metadata
    assert second.state.metadata is shared_metadata
    assert first != second
