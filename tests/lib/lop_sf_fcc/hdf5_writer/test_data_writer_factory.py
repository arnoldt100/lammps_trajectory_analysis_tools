import importlib
from pathlib import Path

import numpy as np
import pytest

import lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer as hdf5_writer
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer import (
    HDF5LopSfFccTrajectoryWriterValueObject,
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
    lop_sf_fcc_data_writer_factory,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_builder_keys import (
    HDF5LopSfFccTrajectoryDataWriterBuilderKey,
    LopSfFccRunMetadataBuilderKey,
    LopSfFccTrajectoryLayoutBuilderKey,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_builders import (
    LopSfFccRunMetadataBuilder,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.exceptions import (
    BuilderKeyError,
    BuilderRegistrationError,
)

EXPECTED_KEYS = frozenset(
    {
        LopSfFccRunMetadataBuilderKey,
        LopSfFccTrajectoryLayoutBuilderKey,
        HDF5LopSfFccTrajectoryDataWriterBuilderKey,
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    }
)


def test_the_factory_registers_exactly_the_documented_keys() -> None:
    assert lop_sf_fcc_data_writer_factory.keys() == EXPECTED_KEYS


def test_the_package_exposes_one_factory_instance() -> None:
    reimported = importlib.import_module(
        "lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer"
    )

    assert reimported.lop_sf_fcc_data_writer_factory is lop_sf_fcc_data_writer_factory


def test_importing_implementation_modules_registers_nothing_further() -> None:
    before = lop_sf_fcc_data_writer_factory.keys()

    importlib.reload(
        importlib.import_module(
            "lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer."
            "lop_sf_fcc_trajectory_writer_builders"
        )
    )
    importlib.reload(
        importlib.import_module(
            "lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer."
            "hdf5_lop_sf_fcc_trajectory_data_writer"
        )
    )

    assert lop_sf_fcc_data_writer_factory.keys() == before


def test_an_unknown_key_raises_a_builder_key_error() -> None:
    with pytest.raises(BuilderKeyError):
        lop_sf_fcc_data_writer_factory.build("no_such_builder")


def test_a_duplicate_registration_raises_and_preserves_the_original() -> None:
    original = lop_sf_fcc_data_writer_factory.build(
        LopSfFccRunMetadataBuilderKey,
        time_step=1.0,
        time_units_label="fs",
        number_of_trajectories=1,
        generation_date=_utc_date(),
        compiler_build_flags=(),
        generating_machine="host",
        lmod_modules=(),
    )

    with pytest.raises(BuilderRegistrationError):
        lop_sf_fcc_data_writer_factory.register_builder(
            LopSfFccRunMetadataBuilderKey, LopSfFccRunMetadataBuilder()
        )

    assert isinstance(original, LopSfFccRunMetadata)
    assert lop_sf_fcc_data_writer_factory.keys() == EXPECTED_KEYS


def test_the_package_factory_builds_a_usable_value_object(
    tmp_path: Path, metadata: LopSfFccRunMetadata, layout: LopSfFccTrajectoryLayout
) -> None:
    target = tmp_path / "package_factory.h5"

    value_object = lop_sf_fcc_data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=target,
        metadata=metadata,
        layout=layout,
    )

    assert isinstance(value_object, HDF5LopSfFccTrajectoryWriterValueObject)
    with value_object as opened:
        opened.append_trajectory_frames(
            0,
            np.array([0], dtype=np.int64),
            np.zeros((1, layout.number_of_atoms, 3)),
            np.zeros((1, layout.number_of_atoms)),
            np.array([[10.0, 10.0, 10.0]]),
            np.array([[90.0, 90.0, 90.0]]),
        )
    assert target.exists()


def test_the_package_exports_its_public_names() -> None:
    for name in hdf5_writer.__all__:
        assert hasattr(hdf5_writer, name)


def _utc_date():
    from datetime import datetime, timezone

    return datetime(2026, 9, 3, tzinfo=timezone.utc)
