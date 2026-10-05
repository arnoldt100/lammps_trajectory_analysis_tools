# Top Level Plan - LOP SF FCC Orchestrator

This is the canonical standing plan for the `lop_sf_fcc` orchestrator feature
(the `LopSfFcc` orchestrator and its builder wiring). It inherits all
project-wide rules from
[../../../top_level_plan.md](../../../top_level_plan.md) and the collection
rules from [../top_level_plan.md](../top_level_plan.md), and adds
feature-specific rules; it must not weaken either level.

## Objective

Maintain `LopSfFcc` as the single orchestration entry point for the FCC
structure-factor local-order-parameter analysis: consume a validated
`CLILopSfFcc` configuration, load all inputs, wire the writer and the
analysis backend, select the execution backend, and run the analysis. The
order-parameter calculation itself is owned by the
`lop_sf_fcc_mdanalysis_workspaces` feature; this module contains no
calculation code.

## Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    lib/
      lop_sf_fcc/
        __init__.py             # registry registration sites + exports
        lop_sf_fcc.py           # LopSfFcc + private setup helpers
        lop_sf_fcc_builder.py   # lop_sf_fcc_builder_key, LopSfFccBuilder

tests/
  test_lop_sf_fcc_end_to_end.py
  test_lop_sf_fcc.py
```

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/
  README.md
  context.md
  top_level_plan.md
```

## Design Rules

- **No physics in the orchestrator:** `lop_sf_fcc.py` must not contain
  order-parameter calculation code; it delegates to `LOP_SF_FCC`. (Migration
  log: the original calculation functions were removed in the Stage 1
  cleanup.)
- **Private state:** every `LopSfFcc` attribute is private with a single
  leading underscore; configuration arrives only through the `CLILopSfFcc`
  argument of `__call__` and is stored in `_set_attributes`.
- **Builder wiring:** `LopSfFccBuilder` is a direct callable builder;
  `lib/lop_sf_fcc/__init__.py` owns exactly two registries
  (`analysis_tool_builder_registry`, `subparser_builder_registry`), each with
  exactly one registration site. `key_lop_sf_fcc` is reserved for future use.
- **Schema validation at the boundary:** `md_params_json` is validated
  against `schemas/md_params.schema.json` (and the metadata file against
  `md_metadata.schema.json`) inside `_set_attributes`, before any universe
  or writer is built. The CLI layer carries only a validated non-blank path.
- **Backend selection is a pure mapping:** `_backend_run_arguments` maps
  `parallel_threads == 1` to `{"backend": "serial"}` and `N > 1` to
  `{"backend": "multiprocessing", "n_workers": N}`, warning when `N` exceeds
  `os.cpu_count()`. `run()` kwargs come only from this function.
- **Debug frame limiting via environment only:** `LTAT_DEBUG_PLOT_FRAMES` is
  read inside `lop_sf_fcc.py` (`_read_debug_plot_frames_env_var`,
  `_resolve_nm_frames_to_compute`); it is not a CLI option. The `lop_sf_fcc`
  subparser help epilog (owned by the command_line feature) documents the
  contract.

## Orchestration Contract (as built)

`LopSfFcc.__call__(command_line_arguments: CLILopSfFcc)`:

1. `_set_attributes`:
   - `parallel_threads` from the CLI object.
   - `_set_md_params_attributes`: validate + read the MD parameters JSON.
   - `_set_md_params_metada_attributes`: validate + read the metadata JSON
     named by `md_params["simulation_parameters"]["simulation_metadata"]`.
   - `_set_universe_attributes`: `load_universe`, then resolve the frame
     count through `LTAT_DEBUG_PLOT_FRAMES`
     (`total_nm_frames` vs. resolved `nm_frames`).
   - `_neighbor_search_radius = np.float32(cutoff)`.
   - `_set_data_writer_attributes`: build the HDF5 writer value object via
     `data_writer_factory` (metadata from `_build_metadata_arguments`,
     layout from `_build_layout_arguments`).
   - `_set_lop_sf_fcc_attribute`: construct `LOP_SF_FCC(universe.atoms,
     edge_length, cutoff, data_writer)`.
2. Print the resolved frame count; compute `run_kwargs` via
   `_backend_run_arguments`; print the selected backend and worker count.
3. Time `self._lop_sf_fcc.run(stop=self._nm_frames, **run_kwargs)` with a
   `LoopTimer` built from `timer_object_factory`.

`LTAT_DEBUG_PLOT_FRAMES` contract: unset, zero, or negative → all frames;
positive `N` ≤ total frames → first `N` frames; non-integer or `N` greater
than the total frame count → `ValueError`.

## Test Plan

- `tests/test_lop_sf_fcc_end_to_end.py`:
  - serial and multiprocessing end-to-end runs produce identical HDF5
    datasets;
  - `_backend_run_arguments` maps `1` → serial, `N > 1` → multiprocessing
    with `n_workers=N`;
  - `N > os.cpu_count()` raises a `RuntimeWarning`.
- `tests/test_lop_sf_fcc.py` (shared with the backend feature): wavevector
  helper values against the Ar4 fixture.
- Frame-limiting behavior is exercised end-to-end in
  `tests/test_lop_sf_fcc_mdanalysis.py`
  (`LTAT_DEBUG_PLOT_FRAMES` honored by `run(stop=...)`); the CLI help epilog
  contract is covered by `tests/test_lop_sf_fcc_cli_parser.py`.

## Non-Goals

- No order-parameter math, pair searches, or accumulators in this module.
- No thread/executor lifecycle here: worker scheduling is delegated to the
  MDAnalysis backend (`n_workers`); per-atom thread-assignment machinery
  lives in the `parallelization` package for future use.
- No new CLI options in this feature; the CLI contract is owned by
  `command_line_workspaces`.
- No HDF5 writing here; writing happens in `LOP_SF_FCC._conclude`.

## Acceptance Criteria

- `LopSfFcc()(CLILopSfFcc(...))` runs end to end and writes a complete,
  correctly structured HDF5 file.
- Serial and parallel runs produce byte-identical datasets.
- Invalid MD-parameter files fail schema validation before any analysis work.
- `lop_sf_fcc.py` contains no calculation functions.
- Focused tests and the full suite pass.

## Migration Log (Completed Work)

### `LTAT_DEBUG_PLOT_FRAMES` debug frame limiting — completed

Converted from `docs/debug_N_frames.md`:

- `_read_debug_plot_frames_env_var()` and `_resolve_nm_frames_to_compute()`
  helpers added, local to `lop_sf_fcc.py` (no CLI flag).
- `_set_universe_attributes` resolves total vs. computed frame counts; the
  legacy hardcoded `max_trajectories_to_compute = 10` loop break was removed
  in favor of slicing/`run(stop=...)`.
- Command-line help follow-up: `LopSfFccSubparserBuilder` epilog +
  `RawDescriptionHelpFormatter` (parser module owned by the command_line
  feature), covered by a parameterized `-h`/`--help` test.

### Parallelization contract (atom-assignment part) — completed (Phase 1)

Converted from `docs/LopSfFcc_parallelization_contract_plan.md`:

- The atom-assignment contract (immutable `tuple[np.ndarray, ...]`, read-only
  arrays, exact/disjoint/complete coverage, deterministic contiguous balanced
  partitioning, empty assignments allowed when `T > N`) was realized as the
  `parallelization` package: `AtomAssignmentProtocol`,
  `AtomThreadAssignment`, and validation helpers. Ownership rules: the
  assignment object never creates threads, owns no atom data, and never
  mutates results.
- Execution-level parallelization went a different route than Phases 2–6
  sketched: instead of per-atom worker partitioning inside the calculation
  functions, `LopSfFcc` parallelizes **over frames** through the MDAnalysis
  multiprocessing backend (see the mdanalysis backend feature's plan).
  `parallel_threads` is therefore wired via `_backend_run_arguments`, and
  `LopSfFcc` never stores an atom-thread assignment.

### Historical note

This plan was converted into an ICM feature workspace on 2026-10-04 and moved
into the `lop_sf_fcc_workspaces` collection as `lop_sf_fcc_orchestrator_workspaces`
later the same day. The original documents at
`docs/LopSfFcc_parallelization_contract_plan.md` and
`docs/debug_N_frames.md` are now pointers to this file.
