# Context - LOP SF FCC Workspaces

Grouping workspace for all features of the `lop_sf_fcc` analysis tool (the
FCC structure-factor local order parameter).

## Purpose

Each child folder is the ICM feature workspace for one stage or backend of
the tool: it holds the feature's README (goal and boundaries), context
(status snapshot), and top-level plan (standing rules and contract).
Production code stays in `src/`; tests stay centralized in `tests/`,
mirroring the feature structure.

## Feature Index

- [lop_sf_fcc_orchestrator_workspaces/](lop_sf_fcc_orchestrator_workspaces/README.md) —
  the `LopSfFcc` orchestrator: consumes `CLILopSfFcc`, loads/validates inputs,
  builds the writer value object, selects the execution backend, times the
  run. Active.
- [lop_sf_fcc_mdanalysis_workspaces/](lop_sf_fcc_mdanalysis_workspaces/README.md) —
  the `LOP_SF_FCC` MDAnalysis backend: single source of the order-parameter
  physics; serial and multiprocessing backends; main-process HDF5 writing.
  Active.
- [lop_sf_fcc_hdf5_writer_workspaces/](lop_sf_fcc_hdf5_writer_workspaces/README.md) —
  the HDF5 trajectory data writer (value object, layout/metadata, builders,
  concrete writer, and the `lop_sf_fcc_data_writer_factory` registry) in
  `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/`. Active.
- [lop_sf_fcc_visit_plotter_workspaces/](lop_sf_fcc_visit_plotter_workspaces/README.md) —
  VisIt-based plotting of the computed order parameter: a time series of 3D
  atom point-clouds pseudocolored by `lop_sf_fcc`, rendered headlessly via a
  VisIt subprocess. Workspace created and plan authored 2026-10-05; no
  production code yet (status: planned).

## Rules

- Dependency direction is one-way: command_line → orchestrator →
  backend/writer/plotter. Cross-feature dependencies are documented in both
  features' READMEs.
- Physics lives only in backend features; writers and plotters consume
  results, they do not compute them.
- Shared rules for all children live in
  [top_level_plan.md](top_level_plan.md) and inherit from
  [../../top_level_plan.md](../../top_level_plan.md).
