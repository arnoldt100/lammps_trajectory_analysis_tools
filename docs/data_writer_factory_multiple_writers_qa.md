# Q&A: Supporting Multiple Concrete Data Writers

This guidance has moved into the lop_sf_fcc HDF5 writer ICM feature workspace
and was updated there: each concrete writer owns its **own** builder registry
in its feature package (registries are never shared across writers). See the
"Adding another concrete writer" section of
[lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md).

This file remains only as a stable link target for existing references; it
carries no content of its own.


