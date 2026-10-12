"""Tests for the HDF5 LOP SF FCC animation source adapter."""

import inspect
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer import (
    HDF5LopSfFccAnimationSource,
    LopSfFccVtkhdfAnimationFrame,
    LopSfFccVtkhdfAnimationSourceInterface,
)

EXPECTED_ABSTRACT_MEMBERS = frozenset(
    {
        "metadata",
        "layout",
        "frame_count",
        "open",
        "frames",
        "close",
        "__enter__",
        "__exit__",
    }
)


def _frame(
    step: int, atom_count: int = 3, offset: float = 0.0
) -> dict[str, np.ndarray]:
    return {
        "step_number": np.asarray([step], dtype=np.int64),
        "positions": (
            offset
            + np.arange(atom_count * 3, dtype=np.float64).reshape(
                1,
                atom_count,
                3,
            )
        ),
        "lop_sf_fcc": (
            offset + np.arange(atom_count, dtype=np.float64).reshape(1, atom_count)
        ),
        "box_lengths": np.asarray([[10.0 + offset, 11.0, 12.0]]),
        "box_angles": np.asarray([[80.0, 90.0, 100.0]]),
    }


def _create_source(
    path: Path,
    *,
    populated: tuple[tuple[int, int], ...] = ((0, 10), (1, 12)),
) -> tuple[LopSfFccRunMetadata, LopSfFccTrajectoryLayout]:
    metadata = LopSfFccRunMetadata(
        time_step=0.5,
        time_units_label="ps",
        number_of_trajectories=3,
        generation_date=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        compiler_build_flags=("-O3",),
        generating_machine="test-host",
        lmod_modules=("gcc/14",),
    )
    layout = LopSfFccTrajectoryLayout(
        number_of_atoms=3,
        length_units_label="angstrom",
    )
    with HDF5LopSfFccTrajectoryDataWriter(path, metadata, layout) as writer:
        for index, step in populated:
            values = _frame(step, offset=float(index))
            writer.append_trajectory_frames(
                index,
                values["step_number"],
                values["positions"],
                values["lop_sf_fcc"],
                values["box_lengths"],
                values["box_angles"],
            )
    return metadata, layout


def test_source_interface_is_state_free_and_abstract() -> None:
    assert LopSfFccVtkhdfAnimationSourceInterface.__slots__ == ()
    assert (
        LopSfFccVtkhdfAnimationSourceInterface.__abstractmethods__
        == EXPECTED_ABSTRACT_MEMBERS
    )
    with pytest.raises(TypeError):
        LopSfFccVtkhdfAnimationSourceInterface()  # type: ignore[abstract]


def test_source_interface_frames_returns_an_iterator() -> None:
    signature = inspect.signature(LopSfFccVtkhdfAnimationSourceInterface.frames)
    assert list(signature.parameters) == ["self"]


def test_frame_is_defensive_and_validated() -> None:
    values = _frame(10)
    frame = LopSfFccVtkhdfAnimationFrame(
        10,
        values["positions"][0],
        values["lop_sf_fcc"][0],
        values["box_lengths"][0],
        values["box_angles"][0],
    )
    positions = frame.positions
    positions[0, 0] = -1.0

    assert frame.step_number == 10
    assert frame.positions[0, 0] == 0.0
    with pytest.raises(DataWriterConfigurationError):
        LopSfFccVtkhdfAnimationFrame(
            -1,
            values["positions"][0],
            values["lop_sf_fcc"][0],
            values["box_lengths"][0],
            values["box_angles"][0],
        )
    with pytest.raises(DataWriterConfigurationError):
        LopSfFccVtkhdfAnimationFrame(
            10,
            values["positions"][0],
            values["lop_sf_fcc"][0, :-1],
            values["box_lengths"][0],
            values["box_angles"][0],
        )


def test_open_derives_metadata_layout_and_ordered_frames(tmp_path: Path) -> None:
    source_path = tmp_path / "source.h5"
    metadata, layout = _create_source(source_path)
    source = HDF5LopSfFccAnimationSource(source_path)

    with source:
        assert source.frame_count == 2
        assert source.metadata.time_step == metadata.time_step
        assert source.metadata.time_units_label == metadata.time_units_label
        assert source.metadata.length_units_label == layout.length_units_label
        assert source.metadata.generation_date == metadata.generation_date
        assert source.layout.number_of_atoms == layout.number_of_atoms
        assert source.layout.position_dtype == layout.position_dtype
        frames = list(source.frames())

    assert [frame.step_number for frame in frames] == [10, 12]
    np.testing.assert_allclose(frames[0].positions, _frame(10)["positions"][0])
    np.testing.assert_allclose(
        frames[1].lop_sf_fcc_values,
        _frame(12, offset=1.0)["lop_sf_fcc"][0],
    )
    with pytest.raises(DataWriterLifecycleError):
        _ = source.metadata


def test_source_requires_open_before_inspection(tmp_path: Path) -> None:
    source = HDF5LopSfFccAnimationSource(tmp_path / "source.h5")

    with pytest.raises(DataWriterLifecycleError):
        _ = source.layout
    with pytest.raises(DataWriterLifecycleError):
        _ = source.frame_count
    with pytest.raises(DataWriterLifecycleError):
        next(source.frames())


def test_source_reports_unopenable_input(tmp_path: Path) -> None:
    with pytest.raises(DataWriterTargetError):
        HDF5LopSfFccAnimationSource(tmp_path / "missing.h5").open()


def test_source_rejects_an_interior_gap(tmp_path: Path) -> None:
    source_path = tmp_path / "gap.h5"
    _create_source(source_path, populated=((1, 12),))

    with pytest.raises(DataWriterConfigurationError, match="follows an empty"):
        HDF5LopSfFccAnimationSource(source_path).open()


def test_source_rejects_multiple_frames_in_one_group(tmp_path: Path) -> None:
    source_path = tmp_path / "multiple.h5"
    metadata, layout = _create_source(source_path, populated=())
    writer = HDF5LopSfFccTrajectoryDataWriter(source_path, metadata, layout)
    writer.open_for_append()
    first = _frame(10)
    second = _frame(12, offset=1.0)
    writer.append_trajectory_frames(
        0,
        np.concatenate([first["step_number"], second["step_number"]]),
        np.concatenate([first["positions"], second["positions"]]),
        np.concatenate([first["lop_sf_fcc"], second["lop_sf_fcc"]]),
        np.concatenate([first["box_lengths"], second["box_lengths"]]),
        np.concatenate([first["box_angles"], second["box_angles"]]),
    )
    writer.close()

    with pytest.raises(DataWriterConfigurationError, match="more than one"):
        HDF5LopSfFccAnimationSource(source_path).open()


def test_source_rejects_nonincreasing_cross_group_steps(tmp_path: Path) -> None:
    source_path = tmp_path / "steps.h5"
    _create_source(source_path, populated=((0, 12), (1, 10)))

    with pytest.raises(DataWriterConfigurationError, match="strictly increasing"):
        HDF5LopSfFccAnimationSource(source_path).open()


def test_source_rejects_missing_dataset_and_inconsistent_units(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing_dataset.h5"
    _create_source(missing_path)
    with h5py.File(missing_path, "r+") as source:
        del source["trajectories"]["traj_00001"]["lop_sf_fcc"]
    with pytest.raises(DataWriterConfigurationError, match="required datasets"):
        HDF5LopSfFccAnimationSource(missing_path).open()

    units_path = tmp_path / "units.h5"
    _create_source(units_path)
    with h5py.File(units_path, "r+") as source:
        source["trajectories"]["traj_00001"]["box_lengths"].attrs["units"] = "nm"
    with pytest.raises(DataWriterConfigurationError, match="length units"):
        HDF5LopSfFccAnimationSource(units_path).open()


def test_source_rejects_invalid_decoded_values(tmp_path: Path) -> None:
    source_path = tmp_path / "invalid_values.h5"
    _create_source(source_path)
    with h5py.File(source_path, "r+") as source:
        source["trajectories"]["traj_00001"]["positions"][0, 0, 0] = np.nan

    source = HDF5LopSfFccAnimationSource(source_path)
    with source, pytest.raises(DataWriterConfigurationError, match="finite"):
        list(source.frames())
