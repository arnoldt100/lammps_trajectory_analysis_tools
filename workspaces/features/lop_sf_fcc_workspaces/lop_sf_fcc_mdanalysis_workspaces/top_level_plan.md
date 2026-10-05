# Top Level Plan - LOP SF FCC MDAnalysis Backend

This is the canonical standing plan for the `LOP_SF_FCC` MDAnalysis backend
feature. It inherits all project-wide rules from
[../../../top_level_plan.md](../../../top_level_plan.md) and the collection
rules from [../top_level_plan.md](../top_level_plan.md), and adds
feature-specific rules; it must not weaken either level.

## Objective

Maintain `LOP_SF_FCC` as the single source of the FCC structure-factor local
order parameter: a `MDAnalysis.analysis.base.AnalysisBase` subclass that
follows the MDAnalysis guidelines (`__init__` / `_prepare` / `_single_frame`
/ `_conclude` contract), supports the `serial` and `multiprocessing`
backends, and keeps all HDF5 writing in the main process.

## Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    lib/
      lop_sf_fcc/
        `lop_sf_fcc_mdanalysis.py`   # LOP_SF_FCC + wavevector/calculation helpers

tests/
  test_lop_sf_fcc_mdanalysis.py
  test_lop_sf_fcc_Ar4Version0.py
  test_lop_sf_fcc.py
```

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_mdanalysis_workspaces/
  README.md
  context.md
  top_level_plan.md
```

## Design Rules

- **Single source of the calculation:** the order-parameter math lives only
  in this module; the orchestrator and tests import it from here, never
  re-implement it.
- **MDAnalysis guidelines:** `__init__(atomgroup, edge_length, cutoff,
  data_writer=None, **kwargs)` calls
  `super().__init__(atomgroup.universe.trajectory, **kwargs)`, computes only
  frame-independent data (wavevectors), and allocates nothing per frame;
  `_prepare` allocates result arrays sized to `self.n_frames` and builds
  per-frame accumulators; `_single_frame` is free of cross-frame state and
  writes only row `self._frame_index`; `_conclude` runs once in the main
  process.
- **Respect the user's selection:** the neighbor search and accumulators
  operate on the analysis `AtomGroup`, not `universe.select_atoms("all")`;
  results are sized to `atomgroup.n_atoms`.
- **Writing only in the main process:** `_single_frame` never writes HDF5.
  `_conclude` opens/appends via the writer value object
  (`__enter__` creates; `open_for_append()` on later runs) and writes rows in
  frame order. `__getstate__` drops `_data_writer` and per-run accumulators
  from pickled copies — but must **not** clear `results` (worker copies are
  pickled back during the merge).
- **Parallel safety:** `_analysis_algorithm_is_parallelizable = True`;
  `get_supported_backends()` returns `('serial', 'multiprocessing')`;
  `_get_aggregator()` stacks every per-frame result
  (`lop_sf_fcc`, `box_lengths`, `box_angles`, `positions`) along the frame
  axis via `ResultsGroup.ndarray_vstack`; `run()` resets `self.results`
  first so stale results are not shipped to workers.
- **No backend leakage:** Dask is out of scope; `verbose` progress is
  serial-only (MDAnalysis raises for non-serial backends).

## Backend Contract (as built)

- `results.lop_sf_fcc`: `(n_frames, n_atoms)` `float64`.
- `results.box_lengths`, `results.box_angles`: `(n_frames, 3)`.
- `results.positions`: `(n_frames, n_atoms, 3)` `float32` (needed so the
  orchestrator never writes from an explicit loop).
- Base-class `frames` and `times` are authoritative for step numbering.
- Accumulators (neighbor counts, raw exp terms, normalized terms) are built
  per `_prepare` through `array_accumulator_builder_registry` and reset per
  frame; `finalize()` returns read-only views copied into the result arrays.
- An atom with no neighbors inside the cutoff yields `0.0`.

## Test Plan

- `tests/test_lop_sf_fcc_mdanalysis.py`: class contract — result shapes for
  full and ranged runs, perfect-FCC expected value, isolated-atom zero,
  `AtomGroup` subset sizing, per-frame box storage, fixture value equality
  (`test_wavevectors_match_fixture`, `test_matches_fixture_values`,
  `test_box_is_stored_per_frame`), HDF5 equality with the explicit-loop
  reference; parallel matrix over `backend="serial"` /
  `backend="multiprocessing"` with `n_workers ∈ {1, 2, 3}` asserting exact
  equality, `n_parts` independence (including empty groups), pickled copies
  have `_data_writer is None`, and `verbose` with a non-serial backend
  raises.
- `tests/test_lop_sf_fcc_Ar4Version0.py`: per-atom `exp(iq·r)` sums and
  normalized values against the fixed Ar4 fixture.
- `tests/test_lop_sf_fcc.py`: wavevector helper values against the fixture.

## Non-Goals

- No HDF5 writing from `_single_frame` or from any worker.
- No Dask backend.
- No per-atom worker partitioning here (that contract lives in the
  `parallelization` package and is superseded by frame-level parallelism).
- No chunking/append-mode orchestration here (the orchestrator may chunk via
  repeated `run()`; `open_for_append()` already supports it).

## Acceptance Criteria

- Serial and multiprocessing results are exactly equal, independent of
  `n_parts` and `n_workers` (including empty groups and `n_workers` greater
  than the frame count).
- HDF5 output is identical across worker counts and is written only in the
  main process.
- `LOP_SF_FCC` results match the fixed Ar4 reference values.
- All focused tests and the full suite pass.

## Migration Log (Completed Work)

Converted from `docs/parallelize_over_trajectories_plan.md`
(status: complete 2026-10-02):

### Stage 1 — serial version — completed

- `LOP_SF_FCC` made a real `AnalysisBase` analysis class; helper functions
  copied from `lop_sf_fcc.py` and adapted to take the analysis `AtomGroup`
  (copied, not imported, to avoid a circular import).
- `_set_lop_sf_fcc_attribute` passes `edge_length`/`cutoff`; `run(stop=...)`
  honors `LTAT_DEBUG_PLOT_FRAMES`; two-frame end-to-end run matches the
  explicit loop to about `5e-10`.
- Stage 1 follow-up: `results.positions` added; HDF5 writing moved into
  `_conclude`; `LopSfFcc.__call__` reduced to `run()` only. On three argon
  frames, all 25 005 HDF5 datasets match the explicit-loop reference exactly
  (maximum absolute difference `0.0`).
- Stage 1 cleanup: the eight dead calculation functions and seven unused
  imports removed from `lop_sf_fcc.py`; tests/fixtures migrated to import
  from this module; reference-comparison tests replaced by fixed fixture
  values. Suite: 311 passed, 2 skipped (at that time).

### Stage 2 — parallel version — completed

- 2.1: `_analysis_algorithm_is_parallelizable = True`, supported backends
  `('serial', 'multiprocessing')`, `_get_aggregator()` with
  `ndarray_vstack` for all four results, `__getstate__` drops the writer and
  per-run accumulators (keeping `results`), `run()` resets results first.
- 2.2: `--parallel-threads` wired through `_backend_run_arguments`; parallel
  test matrix and `tests/test_lop_sf_fcc_end_to_end.py` added. Full suite:
  330 passed, 2 skipped.
- 2.3 regression: 3 argon frames with 1, 2, 3 workers match
  `/tmp/ltat_reference.hdf5` exactly. (Driver scripts must be real files
  guarded by `if __name__ == "__main__":` — with `forkserver`, workers cannot
  import a script read from stdin.)
- 2.3 pilot: 100 argon frames (5849 atoms), `PYTHON_GIL=0 OMP_NUM_THREADS=1
  /usr/bin/time -v` on the 10-core machine; HDF5 output identical for every
  worker count:

  | Workers | Wall time | Speed-up | Parallel efficiency | Max RSS of largest process |
  |---------|-----------|----------|---------------------|----------------------------|
  | 1 (serial) | 502.0 s | 1.00× | 100 % | 349 MB |
  | 2 | 259.5 s | 1.93× | 97 % | 218 MB |
  | 4 | 134.5 s | 3.73× | 93 % | 218 MB |
  | 8 | 90.0 s | 5.58× | 70 % | 217 MB |
  | 10 | 77.8 s | 6.45× | 65 % | 217 MB |

  Serial cost ≈ 5.0 s/frame; scaling near-linear to 4 workers, flattening
  past 8. `/usr/bin/time -v` reports the largest single process.
- 2.3 full run: all 5001 argon frames with 10 workers — 1:00:37 wall time,
  1.48 GB max RSS, 547 MB output, 5001 trajectory groups complete with
  ordered step numbers. Gotcha: unset `LTAT_DEBUG_PLOT_FRAMES` for full runs
  and check the "Number of trajectory frames = 5001" log line.
- 2.4 skipped (justified): peak memory far below the ~21 GB available;
  chunked writing not needed for this example.

### Historical note

This plan was converted into an ICM feature workspace on 2026-10-04 and moved
into the `lop_sf_fcc_workspaces` collection later the same day. The original
document at `docs/parallelize_over_trajectories_plan.md` is now a pointer to
this file.
