# Project Layouts Index

This file serves as the central index for all physical layouts, cells, and blocks within this ICM workspace.

Use it to locate the owning workspace for any production file before reading
or editing code: find the file's feature in the Layout Index below, then read
that feature's `context.md` (current status), `top_level_plan.md` (standing
rules and contract), and `README.md` (goal, boundaries, dependencies) — in
that order, and nothing else unless the feature's own files point further.
This keeps operational context scoped to one feature folder.

## File Roles (every feature folder)

- `README.md` — feature goal, structural boundaries (owned `src/` and
  `tests/` paths), external dependencies, cross-feature dependencies.
- `context.md` — implementation status snapshot (Done/Pending/Not planned),
  decision log, data-flow sketch, maintenance rule.
- `top_level_plan.md` — standing rules, contracts, test plan, non-goals,
  acceptance criteria, migration log. Child plans must not weaken their
  parent plan.

## Workspace Directory Structure

```text
workspaces/
  README.md                      # this file — central index
  context.md                     # ICM root purpose, folder conventions, working rules
  top_level_plan.md              # project-wide engineering rules (all features inherit)
  features/
    command_line_workspaces/     # CLI contract feature
      README.md  context.md  top_level_plan.md
    design_patterns_workspaces/  # collection: domain-neutral design-pattern templates
      context.md  top_level_plan.md
      builder_design_pattern/    # key-based builder/registry template
        README.md  context.md  top_level_plan.md
      value_semantics/           # value-oriented object templates
        README.md  context.md  top_level_plan.md
    lop_sf_fcc_workspaces/       # collection: all lop_sf_fcc tool features
      context.md  top_level_plan.md
      lop_sf_fcc_orchestrator_workspaces/    # LopSfFcc orchestrator
        README.md  context.md  top_level_plan.md
      lop_sf_fcc_mdanalysis_workspaces/      # LOP_SF_FCC MDAnalysis backend
        README.md  context.md  top_level_plan.md
      lop_sf_fcc_hdf5_writer_workspaces/     # HDF5 trajectory writer
        README.md  context.md  top_level_plan.md
```

## Layout Index & Status

| Feature | Workspace | Owned production code | Owned tests | Status |
|---|---|---|---|---|
| command_line | [command_line_workspaces/](features/command_line_workspaces/context.md) | `src/lammps_trajectory_analysis_tools/lib/lammps_analysis_tool_parser.py`, `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc_cli_parser.py`, `src/bin/lammps_analysis_tool.py` | `tests/test_lop_sf_fcc_cli_parser.py` | Active |
| builder_design_pattern | [design_patterns_workspaces/builder_design_pattern/](features/design_patterns_workspaces/builder_design_pattern/context.md) | `src/lammps_trajectory_analysis_tools/design_patterns_templates/builder/` | `tests/design_patterns_templates/builder/` | Active |
| value_semantics | [design_patterns_workspaces/value_semantics/](features/design_patterns_workspaces/value_semantics/context.md) | `src/lammps_trajectory_analysis_tools/design_patterns_templates/value_semantics/` | `tests/design_patterns_templates/value_semantics/` | Active |
| lop_sf_fcc orchestrator | [lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/](features/lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/context.md) | `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/{__init__.py, lop_sf_fcc.py, lop_sf_fcc_builder.py}` | `tests/test_lop_sf_fcc_end_to_end.py`, `tests/test_lop_sf_fcc.py` | Active |
| lop_sf_fcc MDAnalysis backend | [lop_sf_fcc_workspaces/lop_sf_fcc_mdanalysis_workspaces/](features/lop_sf_fcc_workspaces/lop_sf_fcc_mdanalysis_workspaces/context.md) | `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc_mdanalysis.py` | `tests/test_lop_sf_fcc_mdanalysis.py`, `tests/test_lop_sf_fcc_Ar4Version0.py`, `tests/input_files/Ar4Version0.py` | Active |
| lop_sf_fcc HDF5 writer | [lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/](features/lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/context.md) | `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/` | `tests/lib/lop_sf_fcc/hdf5_writer/` | Active |
| lop_sf_fcc VisIt plotter | `lop_sf_fcc_workspaces/lop_sf_fcc_visit_plotter_workspaces/` (not yet created) | TBD | TBD | Planned |

Packages not yet covered by any feature workspace (`accumulator/`,
`parallelization/`, `schemas/`, `integrations/`, `timer_utils/`,
`data_writer_utils/`,
`plotting.py`, `analysis.py`, `trajectory.py`, `utils.py`) are governed
directly by [top_level_plan.md](top_level_plan.md) until their feature
workspaces are created.



