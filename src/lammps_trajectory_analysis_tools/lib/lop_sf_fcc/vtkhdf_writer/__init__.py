"""VTKHDF animation writer for the LOP SF FCC analysis.

This package is the single registration site for
``lop_sf_fcc_vtkhdf_animation_writer_factory``.
"""

from pathlib import Path
from typing import Any

from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.hdf5_lop_sf_fcc_animation_source import (
    HDF5LopSfFccAnimationSource,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_converter import (
    LopSfFccVtkhdfAnimationConverter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_source_interface import (
    LopSfFccVtkhdfAnimationFrame,
    LopSfFccVtkhdfAnimationSourceInterface,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer import (
    LopSfFccVtkhdfAnimationWriter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_builder import (
    HDF5LopSfFccAnimationSourceBuilder,
    LopSfFccVtkhdfAnimationConverterBuilder,
    LopSfFccVtkhdfAnimationLayoutBuilder,
    LopSfFccVtkhdfAnimationMetadataBuilder,
    LopSfFccVtkhdfAnimationWriterBuilder,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilder,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_builder_keys import (
    HDF5LopSfFccAnimationSourceBuilderKey,
    LopSfFccVtkhdfAnimationConverterBuilderKey,
    LopSfFccVtkhdfAnimationLayoutBuilderKey,
    LopSfFccVtkhdfAnimationMetadataBuilderKey,
    LopSfFccVtkhdfAnimationWriterBuilderKey,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LOP_SF_FCC_SOURCE_FORMAT,
    SPATIAL_DIMENSION,
    VTKHDF_DATASET_TYPE,
    VTKHDF_VERSION,
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object import (
    LopSfFccVtkhdfAnimationWriterValueObject,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_interface import (
    LopSfFccVtkhdfAnimationWriterValueObjectInterface,
)

lop_sf_fcc_vtkhdf_animation_writer_factory: BuilderRegistry[Any] = BuilderRegistry()
lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
    LopSfFccVtkhdfAnimationMetadataBuilderKey,
    LopSfFccVtkhdfAnimationMetadataBuilder(),
)
lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
    LopSfFccVtkhdfAnimationLayoutBuilderKey,
    LopSfFccVtkhdfAnimationLayoutBuilder(),
)
lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
    LopSfFccVtkhdfAnimationWriterBuilderKey,
    LopSfFccVtkhdfAnimationWriterBuilder(),
)
lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
    LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilder(
        lop_sf_fcc_vtkhdf_animation_writer_factory
    ),
)
lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
    HDF5LopSfFccAnimationSourceBuilderKey,
    HDF5LopSfFccAnimationSourceBuilder(),
)
lop_sf_fcc_vtkhdf_animation_writer_factory.register_builder(
    LopSfFccVtkhdfAnimationConverterBuilderKey,
    LopSfFccVtkhdfAnimationConverterBuilder(lop_sf_fcc_vtkhdf_animation_writer_factory),
)


def convert_hdf5_lop_sf_fcc_to_vtkhdf(
    source_path: str | Path,
    target_path: str | Path,
    *,
    layout: LopSfFccVtkhdfAnimationLayout | None = None,
) -> Path:
    """Convert one producer HDF5 trajectory file to a VTKHDF animation.

    Args:
        source_path: Persisted LOP SF FCC HDF5 source.
        target_path: Final ``.vtkhdf`` output path.
        layout: Optional output storage and dtype configuration.

    Returns:
        The final target path.
    """
    converter = lop_sf_fcc_vtkhdf_animation_writer_factory.build(
        LopSfFccVtkhdfAnimationConverterBuilderKey
    )
    return converter.convert_hdf5(source_path, target_path, layout=layout)


__all__ = [
    "LOP_SF_FCC_SOURCE_FORMAT",
    "SPATIAL_DIMENSION",
    "VTKHDF_DATASET_TYPE",
    "VTKHDF_VERSION",
    "HDF5LopSfFccAnimationSource",
    "HDF5LopSfFccAnimationSourceBuilder",
    "HDF5LopSfFccAnimationSourceBuilderKey",
    "LopSfFccVtkhdfAnimationConverter",
    "LopSfFccVtkhdfAnimationConverterBuilder",
    "LopSfFccVtkhdfAnimationConverterBuilderKey",
    "LopSfFccVtkhdfAnimationFrame",
    "LopSfFccVtkhdfAnimationLayout",
    "LopSfFccVtkhdfAnimationLayoutBuilder",
    "LopSfFccVtkhdfAnimationLayoutBuilderKey",
    "LopSfFccVtkhdfAnimationMetadata",
    "LopSfFccVtkhdfAnimationMetadataBuilder",
    "LopSfFccVtkhdfAnimationMetadataBuilderKey",
    "LopSfFccVtkhdfAnimationSourceInterface",
    "LopSfFccVtkhdfAnimationWriter",
    "LopSfFccVtkhdfAnimationWriterBuilder",
    "LopSfFccVtkhdfAnimationWriterBuilderKey",
    "LopSfFccVtkhdfAnimationWriterState",
    "LopSfFccVtkhdfAnimationWriterValueObject",
    "LopSfFccVtkhdfAnimationWriterValueObjectBehavior",
    "LopSfFccVtkhdfAnimationWriterValueObjectBuilder",
    "LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey",
    "LopSfFccVtkhdfAnimationWriterValueObjectInterface",
    "convert_hdf5_lop_sf_fcc_to_vtkhdf",
    "lop_sf_fcc_vtkhdf_animation_writer_factory",
]
