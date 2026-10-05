# Top Level Plan - LOP SF FCC VisIt Plotter

This is the canonical standing plan for the LOP SF FCC VisIt plotter feature
(time-series rendering of the computed order parameter). It inherits all
project-wide rules from
[../../../top_level_plan.md](../../../top_level_plan.md) and the collection
rules from [../top_level_plan.md](../top_level_plan.md), and adds
feature-specific rules; it must not weaken either level. Detailed design:
[../../../../docs/lop_sf_fcc_visit_plotter_plan.md](../../../../docs/lop_sf_fcc_visit_plotter_plan.md).

Status: **planned** — no production code yet.

## Objective

Maintain a plotter that turns a LOP SF FCC HDF5 file into a **time series**:
each frame a 3D atom point-cloud of `positions`, pseudocolored by the
per-atom `lop_sf_fcc` order parameter, swept over `step_number`. The plotter
is a read-only consumer of the HDF5 writer feature's output contract.

## Design Rules

- **Subprocess, never in-process:** VisIt is invoked only as
  `visit -cli -nowin -s <script> ...` via `subprocess`. Never `import visit`
  in the project venv (VisIt's bundled Python 3.13 vs the project's
  free-threaded Python 3.14 — ABI and GIL incompatible).
- **Scrub `PYTHON_GIL`:** the launcher removes `PYTHON_GIL` (and
  free-threaded flags) from the subprocess environment; VisIt's Python
  rejects `PYTHON_GIL=0`. A clear error is raised if the GIL check still
  fails.
- **Headless only:** no GUI, no interactive viewer, no `-nowin`-less
  invocations. Version probes use `-cli -nowin -version`.
- **Master `.xdmf` per source HDF5:** the exporter writes one master Xdmf XML
  text file per source file — a temporal collection grid mapping
  `traj_NNNNN` → timestep, with `<Time Value = step_number * time_step>`,
  `PolyVertex` topology (`n_atoms` vertices), `XYZ` geometry referencing
  `positions`, and a `lop_sf_fcc` node attribute. Heavy data is referenced in
  place via HDF5 `DataItem` hyperlinks (small text index, no duplication).
- **Fixed pseudocolor limits across frames** for temporal comparability
  (global min/max of `lop_sf_fcc`, not per-frame auto-scaling).
- **Read-only consumer:** the plotter reads the writer's HDF5 contract; it
  never writes HDF5 and never recomputes physics.
- **Private state:** every plotter/exporter data attribute is private with a
  single leading underscore; access through properties or explicit methods.
- **Builder construction:** the plotter is built through the builder pattern;
  its registry is a `BuilderRegistry` with exactly one registration site in
  the subpackage `__init__.py`.
- **Backend isolation:** VisIt/h5py/export logic stays in this feature;
  physics stays in the backend feature; MDAnalysis is never touched here.

## Exporter / Render Contract (planned)

- Exporter input: path to a LOP SF FCC HDF5 file + export options (frame
  decimation, trajectory→time mapping, dtype). Output: master `.xdmf` path.
- Render input: master `.xdmf`, output directory, image/render options
  (resolution, color table, point size, camera). Output: one PNG per frame
  (optionally an MPEG).
- The launcher returns/raises on the subprocess result; non-zero exit or a
  VisIt GIL failure raises a plotter exception.

## Test Plan

- **Unit (venv; VisIt mocked/faked):** master `.xdmf` well-formedness (XML
  parse; temporal collection; per-timestep dims match `n_atoms`; `lop_sf_fcc`
  attribute present; `<Time>` = `step_number * time_step`); env-scrubbing;
  launcher argument construction; error translation.
- **Integration (strictly opt-in, `LTAT_RUN_VISIT_INTEGRATION=1`,
  skip-if-VisIt-missing):** real headless render of the small argon example →
  non-trivial PNG(s). Disabled by default (it launches a real, non-hermetic
  VisIt subprocess) so `src/bin/run_unit_tests.sh` stays hermetic.
- Tests mirror the package path: `tests/lib/lop_sf_fcc/visit_plotter/`.

## Non-Goals

- No in-process VisIt import, GUI, or interactive mode.
- No physics recomputation; no matplotlib path in this feature.
- No changes to the writer's HDF5 layout.
- No CLI subcommand in the initial implementation (follow-up via the
  command_line feature).

## Acceptance Criteria

- Given a valid LOP SF FCC HDF5 file, the plotter produces a time series of
  per-frame PNGs, each a 3D point cloud pseudocolored by `lop_sf_fcc`, with
  fixed color limits across frames.
- The master `.xdmf` is a valid Xdmf temporal collection that VisIt opens and
  sweeps over time.
- Unit tests pass; the integration test renders the example (when VisIt is
  available); the full suite stays green.

## Migration Log (Completed Work)

- 2026-10-05: feature workspace created; design plan authored in
  [../../../../docs/lop_sf_fcc_visit_plotter_plan.md](../../../../docs/lop_sf_fcc_visit_plotter_plan.md).
  No production code yet.
