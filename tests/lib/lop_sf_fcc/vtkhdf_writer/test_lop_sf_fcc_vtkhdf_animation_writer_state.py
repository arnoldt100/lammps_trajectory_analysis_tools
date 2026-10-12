"""Tests for VTKHDF animation writer value state."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LOP_SF_FCC_SOURCE_FORMAT,
    VTKHDF_DATASET_TYPE,
    VTKHDF_VERSION,
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
    LopSfFccVtkhdfAnimationWriterState,
)


def test_metadata_is_validated_and_hashable(
    metadata: LopSfFccVtkhdfAnimationMetadata,
) -> None:
    metadata.validate()

    assert metadata.source_format == LOP_SF_FCC_SOURCE_FORMAT
    assert metadata.compiler_build_flags == ("-O3", "-march=native")
    assert hash(metadata) == hash(metadata.replace({}))


def test_metadata_attributes_are_defensive(
    metadata: LopSfFccVtkhdfAnimationMetadata,
) -> None:
    attributes = metadata.as_attributes()
    attributes["compiler_build_flags"].append("-g")

    assert metadata.compiler_build_flags == ("-O3", "-march=native")


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"time_step": 0.0}, "time_step"),
        ({"time_step": float("inf")}, "time_step"),
        ({"time_units_label": ""}, "time_units_label"),
        ({"length_units_label": ""}, "length_units_label"),
        (
            {"generation_date": datetime(2026, 1, 1)},
            "timezone-aware",
        ),
        ({"generating_machine": ""}, "generating_machine"),
        ({"compiler_build_flags": ("-O3", 3)}, "compiler_build_flags"),
        ({"lmod_modules": ("gcc", 3)}, "lmod_modules"),
    ],
)
def test_metadata_validation_rejects_invalid_fields(
    metadata: LopSfFccVtkhdfAnimationMetadata,
    changes: dict[str, Any],
    message: str,
) -> None:
    invalid = metadata.replace(changes)

    with pytest.raises(DataWriterConfigurationError, match=message):
        invalid.validate()


def test_metadata_replace_rejects_unknown_fields(
    metadata: LopSfFccVtkhdfAnimationMetadata,
) -> None:
    with pytest.raises(DataWriterConfigurationError, match="unknown metadata"):
        metadata.replace({"source_format": "other"})


def test_layout_exposes_the_phase_one_schema(
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    layout.validate()

    assert layout.vtkhdf_version == VTKHDF_VERSION == (2, 6)
    assert layout.dataset_type == VTKHDF_DATASET_TYPE == "PolyData"
    assert layout.time_dtype == "float64"
    assert layout.connectivity_dtype == "int64"
    assert layout.chunk_shapes["points"] == (4, 3)
    assert layout.dataset_dtypes["lop_sf_fcc"] == "float32"


def test_layout_mappings_are_defensive(
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    dtypes = layout.dataset_dtypes
    chunks = layout.chunk_shapes
    dtypes["points"] = "float64"
    chunks["points"] = (1, 3)

    assert layout.position_dtype == "float32"
    assert layout.chunk_shapes["points"] == (4, 3)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"number_of_atoms": 0}, "number_of_atoms"),
        ({"frames_per_chunk": 0}, "frames_per_chunk"),
        ({"atoms_per_chunk": 0}, "atoms_per_chunk"),
        ({"position_dtype": "int64"}, "position_dtype"),
        ({"lop_sf_fcc_dtype": "int64"}, "lop_sf_fcc_dtype"),
        ({"box_dtype": "int64"}, "box_dtype"),
        ({"step_dtype": "float64"}, "step_dtype"),
        ({"compression_options": 4}, "requires a compression"),
        (
            {"compression": "gzip", "compression_options": ()},
            "must contain integers",
        ),
    ],
)
def test_layout_validation_rejects_invalid_fields(
    layout: LopSfFccVtkhdfAnimationLayout,
    changes: dict[str, Any],
    message: str,
) -> None:
    invalid = layout.replace(changes)

    with pytest.raises(DataWriterConfigurationError, match=message):
        invalid.validate()


def test_layout_is_hashable_and_replacement_is_independent(
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    replaced = layout.replace({"number_of_atoms": 8})

    assert hash(layout) == hash(layout.replace({}))
    assert replaced.number_of_atoms == 8
    assert layout.number_of_atoms == 4


def test_state_accepts_valid_members(
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    state.validate_state()


@pytest.mark.parametrize("file_name", ["animation.h5", "animation", "."])
def test_state_rejects_invalid_target_path(
    state: LopSfFccVtkhdfAnimationWriterState,
    file_name: str,
) -> None:
    invalid = state.replace({"file_path": Path(file_name)})

    with pytest.raises(DataWriterConfigurationError, match="file_path"):
        invalid.validate_state()


def test_state_rejects_invalid_metadata_type(
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    invalid = state.replace({"metadata": object()})

    with pytest.raises(DataWriterConfigurationError, match="metadata must"):
        invalid.validate_state()


def test_state_rejects_invalid_layout_type(
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    invalid = state.replace({"layout": object()})

    with pytest.raises(DataWriterConfigurationError, match="layout must"):
        invalid.validate_state()


def test_state_equality_and_repr_ignore_writer(
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
) -> None:
    carrying = state.with_writer(stub_writer)

    assert carrying == state
    assert "StubWriterProduct" not in repr(carrying)
    assert "writer=" not in repr(carrying)


def test_state_value_fields_participate_in_equality(
    state: LopSfFccVtkhdfAnimationWriterState,
    tmp_path: Path,
) -> None:
    assert state != state.replace({"file_path": tmp_path / "other.vtkhdf"})
    assert state != state.replace(
        {"layout": state.layout.replace({"number_of_atoms": 9})}
    )


def test_state_replace_drops_writer_and_rejects_unknown_fields(
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
    tmp_path: Path,
) -> None:
    replacement = state.with_writer(stub_writer).replace(
        {"file_path": tmp_path / "replacement.vtkhdf"}
    )

    assert replacement.writer is None
    with pytest.raises(DataWriterConfigurationError, match="unknown state"):
        state.replace({"writer": stub_writer})


def test_state_is_immutable_and_unhashable(
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    with pytest.raises(TypeError):
        state.update({"file_path": Path("other.vtkhdf")})
    with pytest.raises(TypeError):
        hash(state)
    with pytest.raises(AttributeError):
        state.file_path = Path("other.vtkhdf")  # type: ignore[misc]
