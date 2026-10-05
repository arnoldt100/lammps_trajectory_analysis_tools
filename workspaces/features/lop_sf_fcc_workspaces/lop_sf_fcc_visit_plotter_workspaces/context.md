# Context - LOP SF FCC VisIt Plotter

Status snapshot for the VisIt plotter feature. Per the ICM rules, this file
must be updated whenever the feature's behavior, data flow, or boundaries
change.

Last reviewed: 2026-10-05.

## Implementation Status

### Done

- Feature workspace created and design plan authored (2026-10-05); see
  [../../../../docs/lop_sf_fcc_visit_plotter_plan.md](../../../../docs/lop_sf_fcc_visit_plotter_plan.md).
- Environment facts verified: VisIt 3.5.0 at `${AT_SW_PACKAGES}/visit`
  (`current -> 3.5.0`); headless `visit -cli -nowin` works only when
  `PYTHON_GIL` is unset (the repo sets `PYTHON_GIL=0` for the free-threaded
  Python 3.14 venv, which VisIt's bundled Python 3.13 rejects). VisIt readers
  include Xdmf/VTK/Silo; its bundled Python has numpy but no h5py.

### Pending

- All production code: `visit_installation.py`,
  `lop_sf_fcc_series_exporter.py`, `visit_render_script.py`,
  `visit_plotter.py`, and the subpackage `__init__.py`.
- Unit tests and the opt-in headless integration test under
  `tests/lib/lop_sf_fcc/visit_plotter/`.
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
