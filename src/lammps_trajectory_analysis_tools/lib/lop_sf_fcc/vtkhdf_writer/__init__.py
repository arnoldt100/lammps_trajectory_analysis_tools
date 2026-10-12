"""VTKHDF animation writer for the LOP SF FCC analysis.

This package is the single registration site for
``lop_sf_fcc_vtkhdf_animation_writer_factory``.
"""

from typing import Any

from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer import (
    LopSfFccVtkhdfAnimationWriter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_builder import (
    LopSfFccVtkhdfAnimationLayoutBuilder,
    LopSfFccVtkhdfAnimationMetadataBuilder,
    LopSfFccVtkhdfAnimationWriterBuilder,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilder,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_builder_keys import (
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

__all__ = [
    "LOP_SF_FCC_SOURCE_FORMAT",
    "SPATIAL_DIMENSION",
    "VTKHDF_DATASET_TYPE",
    "VTKHDF_VERSION",
    "LopSfFccVtkhdfAnimationLayout",
    "LopSfFccVtkhdfAnimationLayoutBuilder",
    "LopSfFccVtkhdfAnimationLayoutBuilderKey",
    "LopSfFccVtkhdfAnimationMetadata",
    "LopSfFccVtkhdfAnimationMetadataBuilder",
    "LopSfFccVtkhdfAnimationMetadataBuilderKey",
    "LopSfFccVtkhdfAnimationWriter",
    "LopSfFccVtkhdfAnimationWriterBuilder",
    "LopSfFccVtkhdfAnimationWriterBuilderKey",
    "LopSfFccVtkhdfAnimationWriterState",
    "LopSfFccVtkhdfAnimationWriterValueObject",
    "LopSfFccVtkhdfAnimationWriterValueObjectBehavior",
    "LopSfFccVtkhdfAnimationWriterValueObjectBuilder",
    "LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey",
    "LopSfFccVtkhdfAnimationWriterValueObjectInterface",
    "lop_sf_fcc_vtkhdf_animation_writer_factory",
]
