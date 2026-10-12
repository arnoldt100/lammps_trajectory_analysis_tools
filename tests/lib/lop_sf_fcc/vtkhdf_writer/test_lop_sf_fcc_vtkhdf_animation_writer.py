"""Tests for the concrete LOP SF FCC VTKHDF animation writer."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer import (
    LopSfFccVtkhdfAnimationWriter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
)


@pytest.fixture
def writer_metadata() -> LopSfFccVtkhdfAnimationMetadata:
    """Return metadata matching the Phase 1 fixture."""
    return LopSfFccVtkhdfAnimationMetadata(
        time_step=0.5,
        time_units_label="ps",
        length_units_label="angstrom",
        generation_date=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        compiler_build_flags=("-O3",),
        generating_machine="test-host",
        lmod_modules=("gcc/14",),
    )


@pytest.fixture
def writer_layout() -> LopSfFccVtkhdfAnimationLayout:
    """Return the three-atom Phase 1 fixture layout."""
    return LopSfFccVtkhdfAnimationLayout(number_of_atoms=3)


@pytest.fixture
def vtkhdf_path(tmp_path: Path) -> Path:
    """Return a unique VTKHDF target path."""
    return tmp_path / "animation.vtkhdf"


@pytest.fixture
def concrete_writer(
    vtkhdf_path: Path,
    writer_metadata: LopSfFccVtkhdfAnimationMetadata,
    writer_layout: LopSfFccVtkhdfAnimationLayout,
) -> Iterator[LopSfFccVtkhdfAnimationWriter]:
    """Return a concrete writer and abort any unclosed staging target."""
    writer = LopSfFccVtkhdfAnimationWriter(
        vtkhdf_path,
        writer_metadata,
        writer_layout,
    )
    yield writer
    writer.abort()


def _frames(
    *,
    frame_count: int = 2,
    first_step: int = 10,
    step_stride: int = 2,
    offset: float = 0.0,
) -> dict[str, np.ndarray[Any, Any]]:
    atom_count = 3
    return {
        "step_number": first_step
        + step_stride * np.arange(frame_count, dtype=np.int64),
        "positions": offset
        + np.arange(
            frame_count * atom_count * 3,
            dtype=np.float64,
        ).reshape(frame_count, atom_count, 3),
        "lop_sf_fcc": offset
        + np.arange(
            frame_count * atom_count,
            dtype=np.float64,
        ).reshape(frame_count, atom_count),
        "box_lengths": np.tile(
            np.asarray([10.0, 10.0, 10.0]),
            (frame_count, 1),
        ),
        "box_angles": np.tile(
            np.asarray([90.0, 90.0, 90.0]),
            (frame_count, 1),
        ),
    }


def _append(
    writer: LopSfFccVtkhdfAnimationWriter,
    frames: dict[str, np.ndarray[Any, Any]],
) -> None:
    writer.append_frames(
        frames["step_number"],
        frames["positions"],
        frames["lop_sf_fcc"],
        frames["box_lengths"],
        frames["box_angles"],
    )


def test_create_stages_then_publishes_on_close(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    staging_path = concrete_writer.configuration["staging_path"]

    concrete_writer.create()

    assert staging_path.exists()
    assert not vtkhdf_path.exists()

    concrete_writer.close()

    assert vtkhdf_path.exists()
    assert not staging_path.exists()


def test_two_step_fixture_matches_the_phase_one_schema(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    frames = _frames()
    with concrete_writer as writer:
        _append(writer, frames)

    with h5py.File(vtkhdf_path, "r") as output:
        assert set(output) == {"LOPSFFCC", "VTKHDF"}
        assert output["LOPSFFCC"].attrs["source_format"] == "lop_sf_fcc_hdf5"
        vtkhdf = output["VTKHDF"]
        assert vtkhdf.attrs["Type"] == b"PolyData"
        np.testing.assert_array_equal(vtkhdf.attrs["Version"], [2, 6])
        assert vtkhdf["Steps"].attrs["NSteps"] == 2
        np.testing.assert_allclose(vtkhdf["Steps"]["Values"], [5.0, 6.0])
        np.testing.assert_array_equal(vtkhdf["NumberOfPoints"], [3, 3])
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["PartOffsets"],
            [0, 1],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["NumberOfParts"],
            [1, 1],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["PointOffsets"],
            [0, 3],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["CellOffsets"],
            [[0, 0, 0, 0], [3, 0, 0, 0]],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["ConnectivityIdOffsets"],
            [[0, 0, 0, 0], [3, 0, 0, 0]],
        )
        np.testing.assert_array_equal(
            vtkhdf["Vertices"]["Connectivity"],
            [0, 1, 2, 0, 1, 2],
        )
        np.testing.assert_array_equal(
            vtkhdf["Vertices"]["Offsets"],
            [0, 1, 2, 3, 0, 1, 2, 3],
        )
        for topology_name in ("Lines", "Polygons", "Strips"):
            topology = vtkhdf[topology_name]
            np.testing.assert_array_equal(topology["NumberOfCells"], [0, 0])
            np.testing.assert_array_equal(
                topology["NumberOfConnectivityIds"],
                [0, 0],
            )
            np.testing.assert_array_equal(topology["Connectivity"], [])
            np.testing.assert_array_equal(topology["Offsets"], [0, 0])
        np.testing.assert_allclose(
            vtkhdf["Points"],
            frames["positions"].astype(np.float32).reshape(6, 3),
        )
        np.testing.assert_allclose(
            vtkhdf["PointData"]["lop_sf_fcc"],
            frames["lop_sf_fcc"].astype(np.float32).reshape(6),
        )
        assert vtkhdf["PointData"]["lop_sf_fcc"].attrs["Attribute"] == b"Scalars"
        np.testing.assert_array_equal(
            vtkhdf["FieldData"]["step_number"],
            [10, 12],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["FieldDataSizes"]["step_number"],
            [[1, 1], [1, 1]],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["FieldDataSizes"]["box_lengths"],
            [[3, 1], [3, 1]],
        )


def test_single_frame_inputs_are_promoted(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    frame = {name: values[0] for name, values in _frames(frame_count=1).items()}
    frame["step_number"] = np.asarray(frame["step_number"]).reshape(())

    with concrete_writer as writer:
        _append(writer, frame)

    with h5py.File(vtkhdf_path, "r") as output:
        assert output["VTKHDF"]["Steps"].attrs["NSteps"] == 1
        assert output["VTKHDF"]["Points"].shape == (3, 3)


def test_append_requires_an_open_target(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
) -> None:
    with pytest.raises(DataWriterLifecycleError):
        _append(concrete_writer, _frames())


def test_create_refuses_existing_final_and_staging_targets(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    vtkhdf_path.touch()
    with pytest.raises(DataWriterTargetError, match="already exists"):
        concrete_writer.create()
    vtkhdf_path.unlink()

    staging_path = concrete_writer.configuration["staging_path"]
    staging_path.touch()
    with pytest.raises(DataWriterTargetError, match="staging target"):
        concrete_writer.create()


def test_context_exception_aborts_without_publishing(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    staging_path = concrete_writer.configuration["staging_path"]

    with pytest.raises(RuntimeError, match="stop"), concrete_writer:
        _append(concrete_writer, _frames(frame_count=1))
        raise RuntimeError("stop")

    assert not vtkhdf_path.exists()
    assert not staging_path.exists()


@pytest.mark.parametrize(
    ("name", "invalid"),
    [
        ("positions", np.zeros((2, 3, 2))),
        ("positions", np.zeros((2, 4, 3))),
        ("lop_sf_fcc", np.zeros((2, 4))),
        ("box_lengths", np.zeros((2, 2))),
        ("box_angles", np.zeros((2, 2))),
        ("step_number", np.zeros((2, 1), dtype=np.int64)),
    ],
)
def test_invalid_shapes_are_rejected_before_mutation(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
    name: str,
    invalid: np.ndarray[Any, Any],
) -> None:
    accepted = _frames(frame_count=1)
    concrete_writer.create()
    _append(concrete_writer, accepted)
    rejected = _frames(frame_count=2, first_step=20)
    rejected[name] = invalid

    with pytest.raises(DataWriterConfigurationError):
        _append(concrete_writer, rejected)
    concrete_writer.close()

    with h5py.File(vtkhdf_path, "r") as output:
        assert output["VTKHDF"]["Steps"].attrs["NSteps"] == 1
        assert output["VTKHDF"]["Points"].shape == (3, 3)


@pytest.mark.parametrize(
    ("name", "mutator", "message"),
    [
        (
            "step_number",
            lambda values: np.asarray([-1, 1], dtype=np.int64),
            "non-negative",
        ),
        (
            "step_number",
            lambda values: np.asarray([10, 10], dtype=np.int64),
            "strictly increasing",
        ),
        (
            "positions",
            lambda values: np.full_like(values, np.nan),
            "finite",
        ),
        (
            "lop_sf_fcc",
            lambda values: np.full_like(values, np.inf),
            "finite",
        ),
        (
            "box_lengths",
            lambda values: np.zeros_like(values),
            "positive",
        ),
        (
            "box_angles",
            lambda values: np.full_like(values, 180.0),
            "strictly between",
        ),
    ],
)
def test_invalid_values_are_rejected(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    name: str,
    mutator: Any,
    message: str,
) -> None:
    frames = _frames()
    frames[name] = mutator(frames[name])
    concrete_writer.create()

    with pytest.raises(DataWriterConfigurationError, match=message):
        _append(concrete_writer, frames)


def test_uncastable_dtypes_and_empty_batches_are_rejected(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
) -> None:
    concrete_writer.create()
    complex_frames = _frames()
    complex_frames["positions"] = complex_frames["positions"].astype(np.complex128)
    with pytest.raises(DataWriterConfigurationError, match="cannot be cast"):
        _append(concrete_writer, complex_frames)

    empty = _frames(frame_count=0)
    with pytest.raises(DataWriterConfigurationError, match="at least one"):
        _append(concrete_writer, empty)


def test_open_for_append_preserves_data_and_extends_offsets(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    first = _frames(frame_count=2)
    second = _frames(frame_count=2, first_step=20, offset=100.0)
    with concrete_writer as writer:
        _append(writer, first)

    concrete_writer.open_for_append()
    _append(concrete_writer, second)
    concrete_writer.close()

    with h5py.File(vtkhdf_path, "r") as output:
        vtkhdf = output["VTKHDF"]
        assert vtkhdf["Steps"].attrs["NSteps"] == 4
        np.testing.assert_array_equal(
            vtkhdf["FieldData"]["step_number"],
            [10, 12, 20, 22],
        )
        np.testing.assert_array_equal(
            vtkhdf["Steps"]["PointOffsets"],
            [0, 3, 6, 9],
        )
        assert vtkhdf["Points"].shape == (12, 3)


def test_append_rejects_non_increasing_stored_boundary(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
) -> None:
    with concrete_writer as writer:
        _append(writer, _frames(frame_count=2))

    concrete_writer.open_for_append()
    with pytest.raises(DataWriterConfigurationError, match="does not follow"):
        _append(concrete_writer, _frames(frame_count=1, first_step=12))


def test_open_for_append_rejects_non_vtkhdf_target(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    with h5py.File(vtkhdf_path, "w") as output:
        output.create_group("other")

    with pytest.raises(DataWriterTargetError, match="no VTKHDF"):
        concrete_writer.open_for_append()


def test_failed_append_open_does_not_remove_unowned_staging_file(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    with h5py.File(vtkhdf_path, "w") as output:
        output.create_group("other")
    staging_path = concrete_writer.configuration["staging_path"]
    staging_path.write_text("unowned")

    with pytest.raises(DataWriterTargetError):
        concrete_writer.open_for_append()

    assert staging_path.read_text() == "unowned"


def test_open_for_append_rejects_layout_and_metadata_mismatches(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
    writer_metadata: LopSfFccVtkhdfAnimationMetadata,
    writer_layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    with concrete_writer as writer:
        _append(writer, _frames(frame_count=1))

    wrong_layout = LopSfFccVtkhdfAnimationWriter(
        vtkhdf_path,
        writer_metadata,
        writer_layout.replace({"number_of_atoms": 4}),
    )
    with pytest.raises(DataWriterConfigurationError):
        wrong_layout.open_for_append()

    wrong_metadata = LopSfFccVtkhdfAnimationWriter(
        vtkhdf_path,
        writer_metadata.replace({"time_step": 1.0}),
        writer_layout,
    )
    with pytest.raises(DataWriterConfigurationError, match="time_step"):
        wrong_metadata.open_for_append()


def test_open_for_append_rejects_extent_inconsistent_with_commit_marker(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    with concrete_writer as writer:
        _append(writer, _frames(frame_count=1))
    with h5py.File(vtkhdf_path, "r+") as output:
        output["VTKHDF"]["Points"].resize((4, 3))

    with pytest.raises(DataWriterConfigurationError, match="Points"):
        concrete_writer.open_for_append()


def test_default_compression_options_reopen_for_append(
    vtkhdf_path: Path,
    writer_metadata: LopSfFccVtkhdfAnimationMetadata,
) -> None:
    layout = LopSfFccVtkhdfAnimationLayout(
        number_of_atoms=3,
        compression="gzip",
    )
    writer = LopSfFccVtkhdfAnimationWriter(
        vtkhdf_path,
        writer_metadata,
        layout,
    )
    with writer:
        _append(writer, _frames(frame_count=1))

    writer.open_for_append()
    _append(writer, _frames(frame_count=1, first_step=20))
    writer.close()

    with h5py.File(vtkhdf_path, "r") as output:
        assert output["VTKHDF"]["Points"].compression == "gzip"
        assert output["VTKHDF"]["Steps"].attrs["NSteps"] == 2


def test_vtk_reader_opens_temporal_polydata(
    concrete_writer: LopSfFccVtkhdfAnimationWriter,
    vtkhdf_path: Path,
) -> None:
    vtk_io = pytest.importorskip("vtkmodules.vtkIOHDF")
    vtk_execution = pytest.importorskip("vtkmodules.vtkCommonExecutionModel")
    with concrete_writer as writer:
        _append(writer, _frames())

    reader = vtk_io.vtkHDFReader()
    reader.SetFileName(str(vtkhdf_path))
    reader.UpdateInformation()
    information = reader.GetOutputInformation(0)
    time_steps_key = vtk_execution.vtkStreamingDemandDrivenPipeline.TIME_STEPS()

    assert information.Length(time_steps_key) == 2
    assert [information.Get(time_steps_key, index) for index in range(2)] == [
        5.0,
        6.0,
    ]
    reader.UpdateTimeStep(5.0)
    output = reader.GetOutput()
    assert output.GetNumberOfPoints() == 3
    assert output.GetPointData().GetArray("lop_sf_fcc") is not None
