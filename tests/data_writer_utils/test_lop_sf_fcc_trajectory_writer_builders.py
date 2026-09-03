from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_builder_keys import (
    HDF5LopSfFccTrajectoryDataWriterBuilderKey,
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    LopSfFccRunMetadataBuilderKey,
    LopSfFccTrajectoryLayoutBuilderKey,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_builders import (
    HDF5LopSfFccTrajectoryDataWriterBuilder,
    HDF5LopSfFccTrajectoryWriterValueObjectBuilder,
    LopSfFccRunMetadataBuilder,
    LopSfFccTrajectoryLayoutBuilder,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object import (
    HDF5LopSfFccTrajectoryWriterValueObject,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    SupportsBuild,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)

METADATA_ARGUMENTS = {
    "time_units": 0.002,
    "time_units_label": "ps",
    "number_of_trajectories": 3,
    "generation_date": datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
    "compiler_build_flags": ("-O3", "-march=native"),
    "generating_machine": "nimzoindian",
    "lmod_modules": ("gcc/13.2.0", "openmpi/4.1.6"),
}
LAYOUT_ARGUMENTS = {"number_of_atoms": 4}


@pytest.fixture
def registry() -> BuilderRegistry:
    built: BuilderRegistry = BuilderRegistry()
    built.register_builder(LopSfFccRunMetadataBuilderKey, LopSfFccRunMetadataBuilder())
    built.register_builder(
        LopSfFccTrajectoryLayoutBuilderKey, LopSfFccTrajectoryLayoutBuilder()
    )
    built.register_builder(
        HDF5LopSfFccTrajectoryDataWriterBuilderKey,
        HDF5LopSfFccTrajectoryDataWriterBuilder(),
    )
    built.register_builder(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        HDF5LopSfFccTrajectoryWriterValueObjectBuilder(built),
    )
    return built


def test_every_builder_satisfies_the_builder_protocol(
    registry: BuilderRegistry,
) -> None:
    builders = [
        LopSfFccRunMetadataBuilder(),
        LopSfFccTrajectoryLayoutBuilder(),
        HDF5LopSfFccTrajectoryDataWriterBuilder(),
        HDF5LopSfFccTrajectoryWriterValueObjectBuilder(registry),
    ]

    for builder in builders:
        assert isinstance(builder, SupportsBuild)


def test_metadata_builder_matches_direct_construction(
    registry: BuilderRegistry,
) -> None:
    built = registry.build(LopSfFccRunMetadataBuilderKey, **METADATA_ARGUMENTS)

    assert built == LopSfFccRunMetadata(**METADATA_ARGUMENTS)


def test_layout_builder_matches_direct_construction(
    registry: BuilderRegistry,
) -> None:
    built = registry.build(LopSfFccTrajectoryLayoutBuilderKey, **LAYOUT_ARGUMENTS)

    assert built == LopSfFccTrajectoryLayout(**LAYOUT_ARGUMENTS)


def test_writer_builder_produces_the_concrete_writer(
    registry: BuilderRegistry,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    built = registry.build(
        HDF5LopSfFccTrajectoryDataWriterBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )

    assert isinstance(built, HDF5LopSfFccTrajectoryDataWriter)
    assert built.configuration["file_path"] == file_path


def test_invalid_arguments_fail_the_same_way_when_built(
    registry: BuilderRegistry,
) -> None:
    invalid = {**METADATA_ARGUMENTS, "time_units": 0.0}

    with pytest.raises(DataWriterConfigurationError):
        registry.build(LopSfFccRunMetadataBuilderKey, **invalid).validate()
    with pytest.raises(DataWriterConfigurationError):
        LopSfFccRunMetadata(**invalid).validate()


def test_composite_builder_returns_a_value_object_holding_no_writer(
    registry: BuilderRegistry, file_path: Path
) -> None:
    value_object = registry.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=METADATA_ARGUMENTS,
        layout=LAYOUT_ARGUMENTS,
    )

    assert isinstance(value_object, HDF5LopSfFccTrajectoryWriterValueObject)
    assert value_object.state.writer is None
    assert value_object.state.file_path == file_path


def test_composite_builder_accepts_pre_built_products(
    registry: BuilderRegistry,
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> None:
    from_objects = registry.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )
    from_arguments = registry.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=METADATA_ARGUMENTS,
        layout=LAYOUT_ARGUMENTS,
    )

    assert from_objects == from_arguments
    assert from_objects.state.metadata is metadata


def test_composite_builder_rejects_invalid_composed_arguments(
    registry: BuilderRegistry, file_path: Path
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        registry.build(
            HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
            file_path=file_path,
            metadata=METADATA_ARGUMENTS,
            layout={"number_of_atoms": 0},
        )


def test_composite_builder_uses_its_injected_registry(file_path: Path) -> None:
    class _StubProduct:
        def __init__(self, **arguments: Any) -> None:
            self.arguments = arguments

    stub_registry: BuilderRegistry = BuilderRegistry()
    stub_registry.register_builder(LopSfFccRunMetadataBuilderKey, _StubProduct)
    stub_registry.register_builder(LopSfFccTrajectoryLayoutBuilderKey, _StubProduct)
    builder = HDF5LopSfFccTrajectoryWriterValueObjectBuilder(stub_registry)

    with pytest.raises(DataWriterConfigurationError):
        builder(file_path, METADATA_ARGUMENTS, LAYOUT_ARGUMENTS)


def test_composite_builder_creates_a_usable_writer_through_the_registry(
    registry: BuilderRegistry, file_path: Path
) -> None:
    value_object = registry.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=METADATA_ARGUMENTS,
        layout=LAYOUT_ARGUMENTS,
    )

    with value_object as opened:
        assert opened.writer_configuration["file_path"] == file_path
    assert file_path.exists()
