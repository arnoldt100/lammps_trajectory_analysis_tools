# LOP SF FCC VisIt Plotter Feature Workspace

## Feature Goal

Own the VisIt-based plotting of the computed FCC structure-factor local order
parameter: read a LOP SF FCC HDF5 file and render a **time series** in which
each frame is a 3D atom point-cloud of `positions`, pseudocolored by the
per-atom `lop_sf_fcc` value, swept over `step_number`.

The plotter is a **read-only consumer** of the HDF5 writer feature's output
contract. Physics and HDF5 writing live in their own sibling features; this
feature owns only plotting. Detailed design:
[../../../../docs/lop_sf_fcc_visit_plotter_plan.md](../../../../docs/lop_sf_fcc_visit_plotter_plan.md).

Status: **active** — exporter, render script, launcher, plotter class,
builders, and registry implemented; unit + integration tests green.

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/visit_plotter/
  __init__.py                        # lop_sf_fcc_visit_plotter_factory
                                     # (single registration site) + exports
  plotter_exceptions.py              # PlotterError hierarchy
  visit_installation.py              # locate/validate the headless VisIt launcher
  lop_sf_fcc_series_exporter.py      # HDF5 -> master .xdmf time series
  visit_render_script.py             # VisIt-side Python source for the subprocess
  visit_plotter_builder_keys.py      # builder key constants
  visit_plotter_builders.py          # installation + plotter builders
  visit_plotter.py                   # LopSfFccVisitPlotter orchestrating class
```

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/lib/lop_sf_fcc/visit_plotter/
  conftest.py
  test_lop_sf_fcc_series_exporter.py
  test_visit_installation.py
  test_visit_plotter.py
  test_visit_plotter_factory.py
  test_visit_render_integration.py   # opt-in: LTAT_RUN_VISIT_INTEGRATION=1, real headless VisIt render
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, the exporter/render contract, the
  environment/GIL rule, test plan, non-goals, acceptance criteria.
- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.

Feature-specific logic must not leak into the global scope: all VisIt, HDF5
export, and render logic lives in the `visit_plotter` subpackage.

## External Dependencies

- **VisIt 3.5.0** (headless) at `${AT_SW_PACKAGES}/visit`
  (`current -> 3.5.0`, launcher `bin/visit`). Invoked only as a subprocess
  (`-cli -nowin`); never imported in-process (its bundled Python 3.13 is
  incompatible with the project's free-threaded Python 3.14 venv and rejects
  `PYTHON_GIL=0`).
- **LOP SF FCC HDF5 writer** (`lop_sf_fcc_hdf5_writer_workspaces`, package
  `lib/lop_sf_fcc/hdf5_writer/`): defines the HDF5 layout this feature reads.
  Read-only dependency on the file contract, not on the writer code.
- **Builder design pattern template** (`design_patterns_templates/builder/`)
  for the plotter builder/registry.
- Third-party: h5py and NumPy (project-side exporter only; VisIt-side script
  uses numpy only).

## Cross-Feature Dependencies

Consumers of this feature: none yet (a future `lammps_analysis_tool`
subcommand in the command_line feature is a documented follow-up).

Dependencies of this feature — each is documented in both workspaces:

- **LOP SF FCC HDF5 writer** (`lop_sf_fcc_hdf5_writer_workspaces`): the
  source of the HDF5 output contract (trajectory groups, datasets, run
  metadata). See
  [../lop_sf_fcc_hdf5_writer_workspaces/README.md](../lop_sf_fcc_hdf5_writer_workspaces/README.md).
- **Builder design pattern** (`design_patterns_workspaces/builder_design_pattern`):
  the plotter registry is a `BuilderRegistry` with a single registration
  site. See
  [../../design_patterns_workspaces/builder_design_pattern/README.md](../../design_patterns_workspaces/builder_design_pattern/README.md).

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Detailed design plan:
  [../../../../docs/lop_sf_fcc_visit_plotter_plan.md](../../../../docs/lop_sf_fcc_visit_plotter_plan.md)
- Collection rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
- HDF5 writer contract:
  [../lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md](../lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md)
