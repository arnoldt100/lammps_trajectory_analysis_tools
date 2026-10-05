# Context - LOP SF FCC VisIt Plotter

Status snapshot for the VisIt plotter feature. Per the ICM rules, this file
must be updated whenever the feature's behavior, data flow, or boundaries
change.

Last reviewed: 2026-10-05.

## Implementation Status

### Done

- Feature workspace created and design plan authored (2026-10-05); see
  [../../../../docs/lop_sf_fcc_visit_plotter_plan.md](../../../../docs/lop_sf_fcc_visit_plotter_plan.md).
- Full implementation in
  `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/visit_plotter/`:
  `plotter_exceptions.py`, `visit_installation.py` (locate/validate the
  headless launcher + scrubbed subprocess env), `lop_sf_fcc_series_exporter.py`
  (HDF5 → master `.xdmf` temporal collection, in-place HDF5 DataItems),
  `visit_render_script.py`, `visit_plotter.py` (orchestrating class), builder
  keys/builders, and the `lop_sf_fcc_visit_plotter_factory` registry (single
  registration site in `__init__.py`).
- Environment facts verified and encoded: VisIt 3.5.0 at
  `${AT_SW_PACKAGES}/visit` (launcher `bin/visit`); headless `visit -cli
  -nowin` with `PYTHON_GIL` scrubbed and `${AT_SW_PACKAGES}/pymol/lib`
  prepended to `LD_LIBRARY_PATH` so `mdserver` resolves `libxml2.so.2`.
- De-risk confirmed end-to-end: VisIt reads the PolyVertex master `.xdmf`
  with in-place HDF5 DataItems and renders per-frame PNGs (verified on the
  argon example through `LopSfFccVisitPlotter.render`).
- Tests: 22 unit tests + 1 opt-in headless integration test under
  `tests/lib/lop_sf_fcc/visit_plotter/`. The integration test is disabled by
  default and runs only when `LTAT_RUN_VISIT_INTEGRATION=1` (it launches a
  real, non-hermetic VisIt subprocess). Default suite: 353 passed, 3 skipped.

### Pending

- Optional follow-up: a `lammps_analysis_tool` subcommand (command_line
  feature) wrapping the plotter.

### Not planned

- In-process `import visit` in the project venv; GUI/interactive mode.
- Physics recomputation; a matplotlib path (this feature is VisIt-only).
- Changes to the writer's HDF5 layout (read-only consumer).

## Decision Log

- **Subprocess bridge:** VisIt's bundled Python 3.13 is ABI/GIL-incompatible
  with the project's free-threaded Python 3.14 venv, so plotting runs as a
  headless `visit -cli -nowin` subprocess with `PYTHON_GIL` scrubbed — never
  an in-process import.
- **Xdmf master file:** one master `.xdmf` temporal collection per source
  HDF5 file; `traj_NNNNN` → timestep; heavy data referenced in place via HDF5
  `DataItem` hyperlinks (small text index).
- **VisIt's Python has no h5py**, so HDF5 reading happens on the project side
  (exporter), and the VisIt-side script only opens the exported `.xdmf`.
- **Fixed pseudocolor limits across frames** for temporal comparability.
- **Library-only first**; CLI subcommand deferred to a follow-up.

## Current Data Flow (planned)

```text
LOP SF FCC HDF5 file (writer feature output, read-only)
  │
  ▼
lop_sf_fcc_series_exporter  (project venv, h5py)
  │ writes master .xdmf (traj_NNNNN -> timestep; in-place HDF5 DataItems)
  ▼
visit_plotter / bridge  (subprocess; env without PYTHON_GIL)
  │ visit -cli -nowin -s visit_render_script.py master.xdmf out_dir ...
  ▼
VisIt 3.5.0 (its own Python 3.13)
  │ Pseudocolor(point mesh, "lop_sf_fcc", fixed limits)
  │ SetTimeSliderState(i) + SaveWindow() per frame
  ▼
PNG per frame (optionally MPEG)
```

## Maintenance Rule

Any change to the plotter contract (the `.xdmf` mapping, the render options,
the launcher's environment handling, or the VisIt interface) requires, in the
same change:

1. Updated focused tests under `tests/lib/lop_sf_fcc/visit_plotter/`.
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of the cross-feature dependency in `README.md` (the HDF5 writer
   feature's file-layout contract).
