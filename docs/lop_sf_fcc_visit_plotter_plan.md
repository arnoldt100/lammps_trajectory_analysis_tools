# LOP SF FCC VisIt Plotter Plan

Status: **planned** (not yet implemented). This document is the design plan
for the `lop_sf_fcc_visit_plotter_workspaces` ICM feature. On conversion to
ICM, the canonical standing plan will be the feature's
`top_level_plan.md`; this file remains the detailed design record.

Branch: `feature/plot-order-parameter`. Date: 2026-10-05.

## Objective

From a LOP SF FCC HDF5 file, produce a **time series** in which each frame is
a **3D atom point-cloud** of `positions`, **pseudocolored by the per-atom
`lop_sf_fcc`** order parameter, swept over `step_number`.

## Confirmed decisions

- **Render kind:** time series of 3D point clouds, pseudocolor by per-atom
  order parameter.
- **Backend:** VisIt 3.5.0, headless, at `${AT_SW_PACKAGES}/visit`
  (`current -> 3.5.0`; launcher `bin/visit`).
- **Export format:** Xdmf, with a **master `.xdmf` XML text file** per source
  HDF5 file (see below).
- **Time mapping:** each `traj_NNNNN` group = one timestep. One temporal
  collection; `traj_00000 .. traj_N` become times `t_0 .. t_N` (matches how
  `LOP_SF_FCC._conclude` currently writes one trajectory group per analysed
  frame).
- **ICM:** new child workspace `lop_sf_fcc_visit_plotter_workspaces/` under
  `lop_sf_fcc_workspaces/`.

## The master `.xdmf` file (explicit requirement)

The exporter writes **one master `.xdmf` XML text file** per source LOP SF
FCC HDF5 file:

- Root `Xdmf`/`Domain` containing a single temporal collection `Grid`
  (`GridType="Collection"`, `CollectionType="Temporal"`).
- Each timestep is a child `Grid` holding:
  - `<Time Value="..."/>` — `step_number * time_step` (root-attribute
    `time_step`).
  - `Topology` of type `PolyVertex`, one vertex per atom
    (`NumberOfElements = n_atoms`).
  - `Geometry` of type `XYZ` referencing that frame's `positions`
    (`(n_atoms, 3)`).
  - `Attribute` (`Center="Node"`) named `lop_sf_fcc` referencing the frame's
    `lop_sf_fcc` (`(n_atoms,)`).
- Heavy data is referenced **in place** via HDF5 `DataItem` hyperlinks, e.g.
  `<DataItem Format="HDF" DataType="Float" Dimensions="N 3">file.h5:/trajectories/traj_00000/positions</DataItem>`,
  so the master `.xdmf` is a small text index with no data duplication.
- A copy-export fallback (values embedded in a companion HDF5 written by the
  exporter) is retained only if in-place referencing proves incompatible with
  the source layout (dtype/rank).

## Architecture — two halves separated by the GIL/ABI boundary

1. **Project-side exporter** (project venv; h5py present): reads the LOP SF
   FCC HDF5 file and emits the master `.xdmf` (+ optional companion data
   file). Package path:
   `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/visit_plotter/`.
2. **VisIt-side render script** (VisIt's bundled Python 3.13; numpy only, no
   h5py): `OpenDatabase(master.xdmf)`, add a Pseudocolor plot on the point
   mesh (point glyph type/size, color table, **fixed min/max across frames**
   for temporal comparability), set camera/annotations, then loop states with
   `SetTimeSliderState(i)` + `SaveWindow()` to write one PNG per frame
   (optionally an MPEG).
3. **Bridge/launcher** (project side):
   `subprocess.run([visit_bin, "-cli", "-nowin", "-s", render_py, master_xdmf,
   out_dir, ...], env=env_without_PYTHON_GIL)`; capture return
   code/stdout/stderr; translate failures into a plotter exception.

## Proposed modules

`src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/visit_plotter/`

| Module | Contents |
| --- | --- |
| `__init__.py` | exports; plotter registry single registration site (if a builder is used) |
| `visit_installation.py` | locate/validate the headless VisIt launcher (`LTAT_VISIT` override → `${AT_SW_PACKAGES}/visit/current/bin/visit`); version probe via `-cli -nowin -version` only (never the bare GUI) |
| `lop_sf_fcc_series_exporter.py` | HDF5 → master `.xdmf` (+ optional companion data file); export-options value object (frame decimation, trajectory→time mapping, dtype) |
| `visit_render_script.py` | the VisIt-side Python source emitted for the subprocess |
| `visit_plotter.py` | orchestrating plotter class (export → launch → collect outputs); private state; built via the builder pattern |

Tests mirror the package path under `tests/lib/lop_sf_fcc/visit_plotter/`.

## Interface / CLI

**Library-only** plotter class first. A `lammps_analysis_tool` subcommand
(wired via the command_line feature) is a documented follow-up, not part of
the initial implementation.

## Environment handling (hard requirement)

The launcher **strips `PYTHON_GIL`** (and free-threaded flags) from the
subprocess environment: the repo env sets `PYTHON_GIL=0` (see
`runtime_env_configuration/core.env.sh` and `src/bin/run_unit_tests.sh`) for
the project's free-threaded Python 3.14 venv, but VisIt's bundled Python 3.13
rejects it (`Disabling the GIL is not supported by this build`). A clear
error is raised if VisIt still fails its GIL check. **No in-process
`import visit`** in the project venv (3.14 free-threaded vs 3.13 ABI/GIL
mismatch).

## Backend isolation

Per the `lop_sf_fcc_workspaces` collection plan: all VisIt/h5py/export logic
stays in this feature; physics stays in the backend feature; the plotter only
**reads** the writer's HDF5 contract. Dependency direction
command_line → orchestrator → plotter is preserved. VisIt subprocess
invocation never touches MDAnalysis.

## Testing strategy

- **Unit (venv; VisIt mocked/faked):** master `.xdmf` well-formed (XML parse;
  temporal collection; per-timestep Topology/Geometry/Attribute dims match
  `n_atoms`; correct `lop_sf_fcc` attribute; `<Time>` = `step_number *
  time_step`); env-scrubbing; launcher argument construction; error
  translation.
- **Integration (opt-in `slow`, skip-if-VisIt-missing):** real headless
  render of
  `examples/example-lop_sf_fcc-ar_box_small/ar_box_small.lop_sf_fcc.nm-frames-1.validated.hdf5`
  → assert non-trivial PNG(s) are produced. Skipped by default so
  `src/bin/run_unit_tests.sh` stays hermetic.

## Non-goals

- No in-process VisIt import; no GUI/interactive mode.
- No physics recomputation; no matplotlib path in this feature.
- No changes to the writer's HDF5 layout (the plotter is a read-only
  consumer).

## Risks / to validate at implementation time

- VisIt 3.5.0 Xdmf **PolyVertex (0-D point) topology** support — if mis-read,
  fall back to legacy numbered `.vtk` point meshes + a `.visit` time index.
- Whether the source HDF5 layout is directly referenceable by HDF5 DataItems
  (float32/float64 dims) or needs a re-exported companion file.
- Global pseudocolor limits across frames (recommended on) for
  frame-to-frame comparability.

## Migration log

- 2026-10-05: plan authored (Plan mode); feature not yet implemented.
