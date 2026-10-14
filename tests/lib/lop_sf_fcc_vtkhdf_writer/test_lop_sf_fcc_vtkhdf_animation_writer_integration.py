"""End-to-end tests for HDF5-to-VTKHDF animation conversion."""

from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer import (
    LopSfFccVtkhdfAnimationLayout,
    convert_hdf5_lop_sf_fcc_to_vtkhdf,
)


def _source_frame(step: int, offset: float) -> dict[str, np.ndarray]:
    return {
        "step_number": np.asarray([step], dtype=np.int64),
        "positions": (offset + np.arange(9, dtype=np.float64).reshape(1, 3, 3)),
        "lop_sf_fcc": (offset + np.asarray([[0.125, 0.5, 0.875]], dtype=np.float64)),
        "box_lengths": np.asarray([[10.0 + offset, 11.0, 12.0]]),
        "box_angles": np.asarray([[80.0, 90.0, 100.0]]),
    }


def _create_realistic_source(path: Path) -> tuple[dict[str, np.ndarray], ...]:
    metadata = LopSfFccRunMetadata(
        time_step=0.5,
        time_units_label="ps",
        number_of_trajectories=3,
        generation_date=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        compiler_build_flags=("-O3", "-march=native"),
        generating_machine="test-host",
        lmod_modules=("gcc/14", "openmpi/5"),
    )
    layout = LopSfFccTrajectoryLayout(
        number_of_atoms=3,
        length_units_label="angstrom",
    )
    frames = (_source_frame(10, 0.0), _source_frame(12, 1.0))
    with HDF5LopSfFccTrajectoryDataWriter(path, metadata, layout) as writer:
        for index, frame in enumerate(frames):
            writer.append_trajectory_frames(
                index,
                frame["step_number"],
                frame["positions"],
                frame["lop_sf_fcc"],
                frame["box_lengths"],
                frame["box_angles"],
            )
    return frames


def test_realistic_hdf5_source_converts_without_scientific_changes(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.h5"
    target_path = tmp_path / "animation.vtkhdf"
    frames = _create_realistic_source(source_path)

    returned = convert_hdf5_lop_sf_fcc_to_vtkhdf(source_path, target_path)

    assert returned == target_path
    with h5py.File(target_path, "r") as output:
        project = output["LOPSFFCC"]
        assert project.attrs["time_step"] == pytest.approx(0.5)
        assert project.attrs["time_units_label"] == "ps"
        assert project.attrs["length_units_label"] == "angstrom"
        assert project.attrs["generating_machine"] == "test-host"

        vtkhdf = output["VTKHDF"]
        assert vtkhdf["Steps"].attrs["NSteps"] == 2
        np.testing.assert_array_equal(
            vtkhdf["FieldData"]["step_number"][:],
            [10, 12],
        )
        np.testing.assert_allclose(vtkhdf["Steps"]["Values"][:], [5.0, 6.0])
        np.testing.assert_array_equal(vtkhdf["NumberOfPoints"][:], [3, 3])
        np.testing.assert_allclose(
            vtkhdf["Points"][:],
            np.concatenate(
                [frame["positions"][0].astype(np.float32) for frame in frames]
            ),
        )
        np.testing.assert_allclose(
            vtkhdf["PointData"]["lop_sf_fcc"][:],
            np.concatenate(
                [frame["lop_sf_fcc"][0].astype(np.float32) for frame in frames]
            ),
        )
        np.testing.assert_allclose(
            vtkhdf["FieldData"]["box_lengths"][:],
            np.concatenate([frame["box_lengths"] for frame in frames]),
        )
        np.testing.assert_allclose(
            vtkhdf["FieldData"]["box_angles"][:],
            np.concatenate([frame["box_angles"] for frame in frames]),
        )


def test_conversion_honors_an_explicit_output_layout(tmp_path: Path) -> None:
    source_path = tmp_path / "source.h5"
    target_path = tmp_path / "compressed.vtkhdf"
    frames = _create_realistic_source(source_path)
    layout = LopSfFccVtkhdfAnimationLayout(
        number_of_atoms=3,
        position_dtype="float64",
        lop_sf_fcc_dtype="float64",
        compression="gzip",
        compression_options=4,
    )

    convert_hdf5_lop_sf_fcc_to_vtkhdf(
        source_path,
        target_path,
        layout=layout,
    )

    with h5py.File(target_path, "r") as output:
        points = output["VTKHDF"]["Points"]
        scalars = output["VTKHDF"]["PointData"]["lop_sf_fcc"]
        assert points.dtype == np.dtype("float64")
        assert scalars.dtype == np.dtype("float64")
        assert points.compression == "gzip"
        np.testing.assert_allclose(
            points[:],
            np.concatenate(
                [frame["positions"][0].astype(np.float32) for frame in frames]
            ),
        )


def test_invalid_later_source_frame_aborts_without_publishing(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "invalid.h5"
    target_path = tmp_path / "animation.vtkhdf"
    _create_realistic_source(source_path)
    with h5py.File(source_path, "r+") as source:
        source["trajectories"]["traj_00001"]["box_lengths"][0, 0] = -1.0

    with pytest.raises(DataWriterConfigurationError, match="positive"):
        convert_hdf5_lop_sf_fcc_to_vtkhdf(source_path, target_path)

    assert not target_path.exists()
    assert not target_path.with_name(f"{target_path.name}.tmp").exists()


def test_output_layout_must_preserve_the_source_atom_count(tmp_path: Path) -> None:
    source_path = tmp_path / "source.h5"
    target_path = tmp_path / "animation.vtkhdf"
    _create_realistic_source(source_path)

    with pytest.raises(DataWriterConfigurationError, match="number_of_atoms"):
        convert_hdf5_lop_sf_fcc_to_vtkhdf(
            source_path,
            target_path,
            layout=LopSfFccVtkhdfAnimationLayout(number_of_atoms=4),
        )

    assert not target_path.exists()


def test_converted_output_opens_with_vtk_reader(tmp_path: Path) -> None:
    vtk = pytest.importorskip("vtk")
    source_path = tmp_path / "source.h5"
    target_path = tmp_path / "animation.vtkhdf"
    _create_realistic_source(source_path)
    convert_hdf5_lop_sf_fcc_to_vtkhdf(source_path, target_path)

    reader = vtk.vtkHDFReader()
    reader.SetFileName(str(target_path))
    reader.UpdateInformation()

    assert (
        reader.GetOutputInformation(0).Length(
            vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS()
        )
        == 2
    )
    reader.UpdateTimeStep(6.0)
    output = reader.GetOutput()
    assert output.GetNumberOfPoints() == 3
    assert output.GetPointData().GetArray("lop_sf_fcc") is not None
