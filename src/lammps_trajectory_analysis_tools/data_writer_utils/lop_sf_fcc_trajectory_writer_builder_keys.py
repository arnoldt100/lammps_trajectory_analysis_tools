#! /usr/bin/env python3
"""Builder keys for the LOP SF FCC trajectory writer products.

This module provides the following public members:
    LopSfFccRunMetadataBuilderKey: Key of the run metadata builder.
    LopSfFccTrajectoryLayoutBuilderKey: Key of the trajectory layout builder.
    HDF5LopSfFccTrajectoryDataWriterBuilderKey: Key of the data writer builder.
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey: Key of the composite
        value object builder.
"""

# ----------
# Public members
# ----------
LopSfFccRunMetadataBuilderKey = "lop_sf_fcc_run_metadata"
LopSfFccTrajectoryLayoutBuilderKey = "lop_sf_fcc_trajectory_layout"
HDF5LopSfFccTrajectoryDataWriterBuilderKey = "hdf5_lop_sf_fcc_trajectory_data_writer"
HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey = (
    "hdf5_lop_sf_fcc_trajectory_writer_value_object"
)

# ----------
# Private members
# ----------

def _main() -> None:
    return


if __name__ == "__main__":
    _main()
