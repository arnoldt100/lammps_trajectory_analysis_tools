import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    MAXIMUM_CHUNK_BYTES,
    MINIMUM_CHUNK_BYTES,
    SPATIAL_DIMENSION,
    LopSfFccTrajectoryLayout,
)


def test_validate_accepts_a_valid_layout(layout: LopSfFccTrajectoryLayout) -> None:
    layout.validate()


@pytest.mark.parametrize(
    "changes",
    [
        {"number_of_atoms": 0},
        {"number_of_atoms": -1},
        {"frames_per_chunk": 0},
        {"atoms_per_chunk": 0},
        {"position_dtype": "not_a_dtype"},
        {"length_units_label": ""},
    ],
)
def test_validate_rejects_invalid_fields(
    layout: LopSfFccTrajectoryLayout, changes: dict
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        layout.replace(changes).validate()


def test_validate_rejects_compression_options_without_a_filter(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        layout.replace({"compression_options": 4}).validate()


def test_validate_accepts_compression_with_options(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    layout.replace({"compression": "gzip", "compression_options": 4}).validate()


def test_validate_rejects_a_chunk_above_the_maximum(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    oversized = layout.replace(
        {"number_of_atoms": 4_000_000, "atoms_per_chunk": 4_000_000}
    )

    with pytest.raises(DataWriterConfigurationError):
        oversized.validate()


def test_validate_rejects_a_needlessly_subdivided_chunk(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    undersized = layout.replace(
        {"number_of_atoms": 500_000, "atoms_per_chunk": 8}
    )

    with pytest.raises(DataWriterConfigurationError):
        undersized.validate()


def test_a_small_layout_is_valid_even_below_the_chunk_floor(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    positions_chunk_bytes = 4 * layout.number_of_atoms * SPATIAL_DIMENSION

    assert positions_chunk_bytes < MINIMUM_CHUNK_BYTES
    layout.validate()


def test_default_production_chunk_sits_inside_the_envelope() -> None:
    production = LopSfFccTrajectoryLayout(number_of_atoms=500_000)
    chunk = production.chunk_shapes["positions"]
    chunk_bytes = 4 * chunk[0] * chunk[1] * chunk[2]

    production.validate()
    assert MINIMUM_CHUNK_BYTES <= chunk_bytes <= MAXIMUM_CHUNK_BYTES


def test_chunk_shapes_are_derived_for_every_dataset() -> None:
    layout = LopSfFccTrajectoryLayout(
        number_of_atoms=500_000, frames_per_chunk=2, atoms_per_chunk=16_384
    )

    assert layout.chunk_shapes == {
        "positions": (2, 16_384, SPATIAL_DIMENSION),
        "lop_sf_fcc": (2, 16_384),
        "box_lengths": (2, SPATIAL_DIMENSION),
        "box_angles": (2, SPATIAL_DIMENSION),
        "step_number": (2,),
    }


def test_atom_chunk_width_is_clamped_to_the_atom_count(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    assert layout.atoms_per_chunk_used == layout.number_of_atoms
    assert layout.chunk_shapes["positions"] == (
        1,
        layout.number_of_atoms,
        SPATIAL_DIMENSION,
    )


def test_frame_shapes_match_the_documented_layout(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    assert layout.frame_shapes == {
        "positions": (layout.number_of_atoms, SPATIAL_DIMENSION),
        "lop_sf_fcc": (layout.number_of_atoms,),
        "box_lengths": (SPATIAL_DIMENSION,),
        "box_angles": (SPATIAL_DIMENSION,),
        "step_number": (),
    }


def test_layout_attributes_cannot_be_assigned(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    with pytest.raises(AttributeError):
        layout.number_of_atoms = 8  # type: ignore[misc]


def test_layouts_compare_by_value_and_are_hashable(
    layout: LopSfFccTrajectoryLayout,
) -> None:
    same = layout.replace({})
    different = layout.replace({"number_of_atoms": layout.number_of_atoms + 1})

    assert same == layout
    assert different != layout
    assert hash(same) == hash(layout)
