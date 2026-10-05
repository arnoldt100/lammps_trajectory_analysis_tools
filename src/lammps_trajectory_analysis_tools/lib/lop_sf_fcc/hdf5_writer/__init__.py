"""HDF5 trajectory writer for the LOP SF FCC analysis.

This package owns the single ``lop_sf_fcc_data_writer_factory`` registry
instance and the one site at which its builders are registered.
"""

from typing import Any

from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
	BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.hdf5_lop_sf_fcc_trajectory_data_writer import (
	HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_behavior import (
	LopSfFccTrajectoryWriterBehavior,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_builder_keys import (
	HDF5LopSfFccTrajectoryDataWriterBuilderKey,
	HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
	LopSfFccRunMetadataBuilderKey,
	LopSfFccTrajectoryLayoutBuilderKey,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_builders import (
	HDF5LopSfFccTrajectoryDataWriterBuilder,
	HDF5LopSfFccTrajectoryWriterValueObjectBuilder,
	LopSfFccRunMetadataBuilder,
	LopSfFccTrajectoryLayoutBuilder,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_state import (
	LopSfFccRunMetadata,
	LopSfFccTrajectoryLayout,
	LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_value_object import (
	HDF5LopSfFccTrajectoryWriterValueObject,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer.lop_sf_fcc_trajectory_writer_value_object_interface import (
	LopSfFccTrajectoryWriterValueObjectInterface,
)

lop_sf_fcc_data_writer_factory: BuilderRegistry[Any] = BuilderRegistry()
lop_sf_fcc_data_writer_factory.register_builder(
	LopSfFccRunMetadataBuilderKey,
	LopSfFccRunMetadataBuilder(),
)
lop_sf_fcc_data_writer_factory.register_builder(
	LopSfFccTrajectoryLayoutBuilderKey,
	LopSfFccTrajectoryLayoutBuilder(),
)
lop_sf_fcc_data_writer_factory.register_builder(
	HDF5LopSfFccTrajectoryDataWriterBuilderKey,
	HDF5LopSfFccTrajectoryDataWriterBuilder(),
)
lop_sf_fcc_data_writer_factory.register_builder(
	HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
	HDF5LopSfFccTrajectoryWriterValueObjectBuilder(lop_sf_fcc_data_writer_factory),
)

__all__ = [
	"HDF5LopSfFccTrajectoryDataWriter",
	"HDF5LopSfFccTrajectoryDataWriterBuilder",
	"HDF5LopSfFccTrajectoryDataWriterBuilderKey",
	"HDF5LopSfFccTrajectoryWriterValueObject",
	"HDF5LopSfFccTrajectoryWriterValueObjectBuilder",
	"HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey",
	"LopSfFccRunMetadata",
	"LopSfFccRunMetadataBuilder",
	"LopSfFccRunMetadataBuilderKey",
	"LopSfFccTrajectoryLayout",
	"LopSfFccTrajectoryLayoutBuilder",
	"LopSfFccTrajectoryLayoutBuilderKey",
	"LopSfFccTrajectoryWriterBehavior",
	"LopSfFccTrajectoryWriterState",
	"LopSfFccTrajectoryWriterValueObjectInterface",
	"lop_sf_fcc_data_writer_factory",
]
