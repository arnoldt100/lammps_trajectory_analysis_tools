"""Backend-neutral data writer interface and shared writer errors.

This package owns the generic writer contract: the writer protocol, the
contract-level exception hierarchy, and the generic single-stream HDF5 writer.
Concrete writers for specific analyses live with the owning feature package
(for example, the LOP SF FCC trajectory writer lives in
``lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer``).
"""

from lammps_trajectory_analysis_tools.data_writer_utils.data_writer_protocol import (
	DataWriterProtocol,
)
from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
	DataWriterConfigurationError,
	DataWriterError,
	DataWriterLifecycleError,
	DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_data_writer import (
	HDF5DataWriter,
)

__all__ = [
	"DataWriterConfigurationError",
	"DataWriterError",
	"DataWriterLifecycleError",
	"DataWriterProtocol",
	"DataWriterTargetError",
	"HDF5DataWriter",
]
