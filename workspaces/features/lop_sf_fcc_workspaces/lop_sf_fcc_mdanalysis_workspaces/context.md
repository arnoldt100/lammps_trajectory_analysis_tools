# Context - LOP SF FCC MDAnalysis Backend

Status snapshot for the `LOP_SF_FCC` MDAnalysis backend feature. Per the ICM
rules, this file must be updated whenever the feature's behavior, data flow,
or boundaries change.

Last reviewed: 2026-10-04.

## Implementation Status

### Done

- `LOP_SF_FCC` is a complete `AnalysisBase` analysis class: wavevectors in
  `__init__`, result allocation and accumulator construction in `_prepare`,
  state-free `_single_frame` writing row `self._frame_index`, and main-process
  HDF5 writing in `_conclude` (create on first `run()`, `open_for_append()`
  afterwards).
- Parallel support: `serial` and `multiprocessing` backends,
  `_analysis_algorithm_is_parallelizable = True`, `_get_aggregator()` with
  `ndarray_vstack` for `lop_sf_fcc`/`box_lengths`/`box_angles`/`positions`,
  `__getstate__` strips writer and accumulators (not `results`), `run()`
  resets results first.
- Calculation helpers are the single source of the physics; the orchestrator
  module contains none.
- Tests: class contract, Ar4 fixture values, perfect-FCC value,
  isolated-atom zero, subset sizing, box-per-frame storage, parallel matrix
  (serial/multiprocessing × workers 1–3, `n_parts` independence, empty
  groups, pickled writer drop, verbose restriction), HDF5 equality.
- Verified against reference: 3-frame argon output matches
  `/tmp/ltat_reference.hdf5` exactly for 1–3 workers; full 5001-frame run
  with 10 workers complete and ordered (see the pilot/full-run numbers in
  `top_level_plan.md`).
- Feature workspace converted to ICM on 2026-10-04 and moved into the
  `lop_sf_fcc_workspaces` collection later the same day; the former canonical
  document `docs/parallelize_over_trajectories_plan.md` is now a pointer
  here.

### Pending

- Nothing open for the serial/parallel contract itself. Future candidates
  (only with demonstrated need): Dask backend evaluation, chunked-run memory
  control (`open_for_append()` is ready), sparse accumulator storage.

### Not planned

- HDF5 writing from `_single_frame` or workers.
- Per-atom worker partitioning inside the calculation functions.
- Re-introducing calculation code into `lop_sf_fcc.py`.

## Decision Log

- Helper functions were **copied** (not imported) from `lop_sf_fcc.py` during
  Stage 1 to avoid a circular import; the originals were then deleted in the
  Stage 1 cleanup so this module is the single source.
- Writing lives in `_conclude` because it runs once, in the main process,
  after worker result aggregation — the same code path therefore works for
  serial and parallel backends and writes in frame order.
- `__getstate__` must not clear `results`: worker copies are pickled back to
  the main process during the merge and their results would be lost.
- `verbose` is serial-only because MDAnalysis raises for non-serial backends.
- Parallelization is over frames (MDAnalysis split-apply-combine), not over
  atoms; the atom-assignment machinery lives in the `parallelization` package
  and currently has no production consumer.

## Current Data Flow

```text
LOP_SF_FCC(atomgroup, edge_length, cutoff, data_writer)
  │ __init__: wavevectors from edge_length (frame-independent)
  ▼
run(stop=nm_frames, backend=..., n_workers=...)
  │ main process: _setup_frames → n_frames; split frames into groups
  ├─ serial: _prepare → per-frame _single_frame
  └─ multiprocessing: pickle copies → each worker _prepare + _single_frame
                       for its group (workers never see the writer)
  │
  ▼ main process: _get_aggregator().merge(...) stacks results in frame order
_conclude: open/create writer value object, append all rows in frame order
```

`_single_frame` per frame: reset accumulators → neighbor search on the
atomgroup → no-coeffs/with-coeffs calculation → copy finalized read-only
accumulator views into `results` row → store box lengths/angles/positions.

## Maintenance Rule

Any change to the backend contract (result arrays, backends, aggregation,
pickling behavior, or the calculation helpers) requires, in the same change:

1. Updated focused tests (`tests/test_lop_sf_fcc_mdanalysis.py`,
   `tests/test_lop_sf_fcc_Ar4Version0.py`, `tests/test_lop_sf_fcc.py`).
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every cross-feature workspace listed in `README.md`
   (lop_sf_fcc orchestrator; accumulator package per its own plans).
