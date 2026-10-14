"""Tests for VTKHDF writer builders, keys, registry, and exports."""

import importlib
from pathlib import Path

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    SupportsBuild,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.exceptions import (
    BuilderKeyError,
    BuilderRegistrationError,
)
from lammps_trajectory_analysis_tools.lib import lop_sf_fcc_vtkhdf_writer
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer import (
    HDF5LopSfFccAnimationSource,
    HDF5LopSfFccAnimationSourceBuilder,
    HDF5LopSfFccAnimationSourceBuilderKey,
    LopSfFccVtkhdfAnimationConverter,
    LopSfFccVtkhdfAnimationConverterBuilder,
    LopSfFccVtkhdfAnimationConverterBuilderKey,
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationLayoutBuilder,
    LopSfFccVtkhdfAnimationLayoutBuilderKey,
    LopSfFccVtkhdfAnimationMetadata,
    LopSfFccVtkhdfAnimationMetadataBuilder,
    LopSfFccVtkhdfAnimationMetadataBuilderKey,
    LopSfFccVtkhdfAnimationWriter,
    LopSfFccVtkhdfAnimationWriterBuilder,
    LopSfFccVtkhdfAnimationWriterBuilderKey,
    LopSfFccVtkhdfAnimationWriterValueObject,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilder,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
    lop_sf_fcc_vtkhdf_animation_writer_factory,
)

EXPECTED_KEYS = frozenset(
    {
        HDF5LopSfFccAnimationSourceBuilderKey,
        LopSfFccVtkhdfAnimationConverterBuilderKey,
        LopSfFccVtkhdfAnimationMetadataBuilderKey,
        LopSfFccVtkhdfAnimationLayoutBuilderKey,
        LopSfFccVtkhdfAnimationWriterBuilderKey,
        LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
    }
)


def test_all_builders_satisfy_the_builder_protocol() -> None:
    builders = (
        LopSfFccVtkhdfAnimationMetadataBuilder(),
        LopSfFccVtkhdfAnimationLayoutBuilder(),
        LopSfFccVtkhdfAnimationWriterBuilder(),
        LopSfFccVtkhdfAnimationWriterValueObjectBuilder(
            lop_sf_fcc_vtkhdf_animation_writer_factory
        ),
        HDF5LopSfFccAnimationSourceBuilder(),
        LopSfFccVtkhdfAnimationConverterBuilder(
            lop_sf_fcc_vtkhdf_animation_writer_factory
        ),
    )

    assert all(isinstance(builder, SupportsBuild) for builder in builders)


def test_factory_registers_exactly_the_six_documented_keys() -> None:
    assert lop_sf_fcc_vtkhdf_animation_writer_factory.keys() == EXPECTED_KEYS


def test_factory_builds_metadata_and_layout(
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    built_metadata = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationMetadataBuilderKey,
        time_step=metadata.time_step,
        time_units_label=metadata.time_units_label,
        length_units_label=metadata.length_units_label,
        generation_date=metadata.generation_date,
        compiler_build_flags=metadata.compiler_build_flags,
        generating_machine=metadata.generating_machine,
        lmod_modules=metadata.lmod_modules,
    )
    built_layout = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationLayoutBuilderKey,
        number_of_atoms=layout.number_of_atoms,
    )

    assert built_metadata == metadata
    assert built_layout == layout


def test_factory_builds_the_concrete_writer(
    file_path: Path,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    writer = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationWriterBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )

    assert isinstance(writer, LopSfFccVtkhdfAnimationWriter)
    assert writer.configuration["file_path"] == file_path


def test_factory_builds_the_source_and_converter(tmp_path: Path) -> None:
    source_path = tmp_path / "source.h5"
    source = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        HDF5LopSfFccAnimationSourceBuilderKey,
        file_path=source_path,
    )
    converter = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationConverterBuilderKey
    )

    assert isinstance(source, HDF5LopSfFccAnimationSource)
    assert source.file_path == source_path
    assert isinstance(converter, LopSfFccVtkhdfAnimationConverter)


def test_composite_builder_accepts_values_and_argument_mappings(
    file_path: Path,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    from_values = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )
    from_mappings = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata={
            "time_step": metadata.time_step,
            "time_units_label": metadata.time_units_label,
            "length_units_label": metadata.length_units_label,
            "generation_date": metadata.generation_date,
            "compiler_build_flags": metadata.compiler_build_flags,
            "generating_machine": metadata.generating_machine,
            "lmod_modules": metadata.lmod_modules,
        },
        layout={"number_of_atoms": layout.number_of_atoms},
    )

    assert isinstance(from_values, LopSfFccVtkhdfAnimationWriterValueObject)
    assert from_values == from_mappings
    assert from_values.state.writer is None


def test_package_factory_builds_a_usable_value_object(
    file_path: Path,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    value_object = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )
    with value_object:
        value_object.append_frames(
            np.asarray([0], dtype=np.int64),
            np.zeros((1, layout.number_of_atoms, 3)),
            np.zeros((1, layout.number_of_atoms)),
            np.asarray([[10.0, 10.0, 10.0]]),
            np.asarray([[90.0, 90.0, 90.0]]),
        )
    value_object.open_for_append()
    value_object.append_frames(
        np.asarray([1], dtype=np.int64),
        np.ones((1, layout.number_of_atoms, 3)),
        np.ones((1, layout.number_of_atoms)),
        np.asarray([[10.0, 10.0, 10.0]]),
        np.asarray([[90.0, 90.0, 90.0]]),
    )
    value_object.close()

    with h5py.File(file_path, "r") as output:
        assert output["VTKHDF"]["Steps"].attrs["NSteps"] == 2
        np.testing.assert_array_equal(
            output["VTKHDF"]["Steps"]["Values"][:],
            [0.0, metadata.time_step],
        )


def test_package_factory_value_object_aborts_after_context_exception(
    file_path: Path,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    value_object = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )

    with pytest.raises(RuntimeError, match="stop"), value_object:
        raise RuntimeError("stop")

    assert not file_path.exists()


def test_registry_is_owned_only_by_package_init() -> None:
    before = lop_sf_fcc_vtkhdf_animation_writer_factory.keys()
    for module_name in (
        "lop_sf_fcc_vtkhdf_animation_writer_builder",
        "lop_sf_fcc_vtkhdf_animation_writer_builder_keys",
        "lop_sf_fcc_vtkhdf_animation_converter",
        "lop_sf_fcc_vtkhdf_animation_source_interface",
        "lop_sf_fcc_vtkhdf_animation_writer_value_object",
        "hdf5_lop_sf_fcc_animation_source",
    ):
        importlib.reload(
            importlib.import_module(
                "lammps_trajectory_analysis_tools.lib."
                f"lop_sf_fcc_vtkhdf_writer.{module_name}"
            )
        )

    assert lop_sf_fcc_vtkhdf_animation_writer_factory.keys() == before


def test_duplicate_and_unknown_keys_use_registry_errors() -> None:
    with pytest.raises(BuilderKeyError):
        lop_sf_fcc_vtkhdf_animation_writer_factory.build("unknown")
    with pytest.raises(BuilderRegistrationError):
        lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
            LopSfFccVtkhdfAnimationMetadataBuilderKey,
            LopSfFccVtkhdfAnimationMetadataBuilder(),
        )
    assert lop_sf_fcc_vtkhdf_animation_writer_factory.keys() == EXPECTED_KEYS


def test_package_exports_every_documented_name() -> None:
    assert lop_sf_fcc_vtkhdf_writer.__all__
    assert all(
        hasattr(lop_sf_fcc_vtkhdf_writer, name)
        for name in lop_sf_fcc_vtkhdf_writer.__all__
    )
