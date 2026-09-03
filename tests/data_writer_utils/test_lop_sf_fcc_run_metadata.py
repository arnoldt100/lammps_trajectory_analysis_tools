from datetime import datetime, timezone

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccRunMetadata,
)


def test_validate_accepts_a_fully_populated_metadata_value(
    metadata: LopSfFccRunMetadata,
) -> None:
    metadata.validate()


@pytest.mark.parametrize(
    "changes",
    [
        {"time_units": 0.0},
        {"time_units": -1.0},
        {"number_of_trajectories": 0},
        {"number_of_trajectories": -2},
        {"generating_machine": ""},
        {"time_units_label": ""},
        {"generation_date": datetime(2026, 9, 3, 12, 0)},
    ],
)
def test_validate_rejects_invalid_scalar_fields(
    metadata: LopSfFccRunMetadata, changes: dict
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        metadata.replace(changes).validate()


@pytest.mark.parametrize(
    "changes",
    [
        {"compiler_build_flags": ("-O3", 3)},
        {"lmod_modules": (None,)},
    ],
)
def test_validate_rejects_non_string_sequence_entries(
    metadata: LopSfFccRunMetadata, changes: dict
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        metadata.replace(changes).validate()


def test_metadata_attributes_cannot_be_assigned(
    metadata: LopSfFccRunMetadata,
) -> None:
    with pytest.raises(AttributeError):
        metadata.time_units = 1.0  # type: ignore[misc]


def test_equal_field_values_compare_equal_and_metadata_is_hashable(
    metadata: LopSfFccRunMetadata,
) -> None:
    same = metadata.replace({})
    different = metadata.replace({"generating_machine": "ruylopez"})

    assert same == metadata
    assert different != metadata
    assert hash(same) == hash(metadata)
    assert len({metadata, same, different}) == 2


def test_sequence_fields_are_stored_as_tuples(metadata: LopSfFccRunMetadata) -> None:
    from_lists = metadata.replace(
        {"compiler_build_flags": ["-O2"], "lmod_modules": ["gcc/13.2.0"]}
    )

    assert isinstance(from_lists.compiler_build_flags, tuple)
    assert isinstance(from_lists.lmod_modules, tuple)


def test_as_attributes_reports_every_required_metadata_name(
    metadata: LopSfFccRunMetadata,
) -> None:
    attributes = metadata.as_attributes()

    assert set(attributes) == {
        "time_units",
        "time_units_label",
        "number_of_trajectories",
        "generation_date",
        "compiler_build_flags",
        "generating_machine",
        "lmod_modules",
    }


def test_metadata_attributes_round_trip_through_hdf5(
    metadata: LopSfFccRunMetadata, tmp_path
) -> None:
    target = tmp_path / "attributes.h5"

    with h5py.File(target, "w") as output:
        for name, value in metadata.as_attributes().items():
            output.attrs[name] = value

    with h5py.File(target, "r") as output:
        assert output.attrs["time_units"] == pytest.approx(metadata.time_units)
        assert output.attrs["number_of_trajectories"] == metadata.number_of_trajectories
        assert output.attrs["generating_machine"] == metadata.generating_machine
        assert output.attrs["generation_date"] == metadata.generation_date.isoformat()
        np.testing.assert_array_equal(
            output.attrs["compiler_build_flags"],
            np.array(metadata.compiler_build_flags, dtype=object),
        )
        np.testing.assert_array_equal(
            output.attrs["lmod_modules"],
            np.array(metadata.lmod_modules, dtype=object),
        )


def test_generation_date_may_use_any_timezone() -> None:
    metadata = LopSfFccRunMetadata(
        time_units=1.0,
        time_units_label="fs",
        number_of_trajectories=1,
        generation_date=datetime(2026, 9, 3, tzinfo=timezone.utc),
        compiler_build_flags=(),
        generating_machine="host",
        lmod_modules=(),
    )

    metadata.validate()
