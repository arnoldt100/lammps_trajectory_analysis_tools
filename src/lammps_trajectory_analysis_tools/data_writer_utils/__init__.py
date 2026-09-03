"""Data writer utilities and the data writer builder registry.

This package owns the single ``data_writer_factory`` registry instance and the
one site at which its builders are registered.
"""

from typing import Any

from lammps_trajectory_analysis_tools.data_writer_utils.data_writer_protocol import (
	DataWriterProtocol,
)
from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
	DataWriterConfigurationError,
	DataWriterError,
	DataWriterLifecycleError,
	DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
	HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_behavior import (
	LopSfFccTrajectoryWriterBehavior,
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
	LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object import (
	HDF5LopSfFccTrajectoryWriterValueObject,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object_interface import (
	LopSfFccTrajectoryWriterValueObjectInterface,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
	BuilderRegistry,
)

data_writer_factory: BuilderRegistry[Any] = BuilderRegistry()
data_writer_factory.register_builder(
	LopSfFccRunMetadataBuilderKey,
	LopSfFccRunMetadataBuilder(),
)
data_writer_factory.register_builder(
	LopSfFccTrajectoryLayoutBuilderKey,
	LopSfFccTrajectoryLayoutBuilder(),
)
data_writer_factory.register_builder(
	HDF5LopSfFccTrajectoryDataWriterBuilderKey,
	HDF5LopSfFccTrajectoryDataWriterBuilder(),
)
data_writer_factory.register_builder(
	HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
	HDF5LopSfFccTrajectoryWriterValueObjectBuilder(data_writer_factory),
)

__all__ = [
	"DataWriterConfigurationError",
	"DataWriterError",
	"DataWriterLifecycleError",
	"DataWriterProtocol",
	"DataWriterTargetError",
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
	"data_writer_factory",
]
