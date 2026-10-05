# Context - LOP SF FCC Orchestrator

Status snapshot for the `lop_sf_fcc` orchestrator feature. Per the ICM
rules, this file must be updated whenever the feature's behavior, data flow,
or boundaries change.

Last reviewed: 2026-10-04.

## Implementation Status

### Done

- Orchestrator: `LopSfFcc.__call__` consumes `CLILopSfFcc`, loads and
  validates MD parameters/metadata, loads the universe, builds the HDF5
  writer value object, constructs `LOP_SF_FCC`, selects the backend, and
  times the run. No calculation code remains in `lop_sf_fcc.py` (Stage 1
  cleanup removed the eight dead functions and unused imports; HDF5 output
  verified unchanged).
- Builder wiring: `analysis_tool_builder_registry` and
  `subparser_builder_registry` owned by `lib/lop_sf_fcc/__init__.py`;
  `LopSfFccBuilder` registered under `lop_sf_fcc_builder_key`;
  `key_lop_sf_fcc` reserved.
- Backend selection: `_backend_run_arguments` maps `parallel_threads`
  `1 → serial`, `N > 1 → multiprocessing` with `n_workers=N`, warning past
  `os.cpu_count()`. Covered by `tests/test_lop_sf_fcc_end_to_end.py`,
  including identical serial/parallel HDF5 output.
- Debug frame limiting: `LTAT_DEBUG_PLOT_FRAMES` honored via
  `_read_debug_plot_frames_env_var`/`_resolve_nm_frames_to_compute`;
  subparser help epilog documents the contract.
- Full-run verification (2026-10-04): all 5001 argon frames with
  `--parallel-threads 10`, 1:00:37 wall time, 1.48 GB max RSS, 547 MB output,
  datasets complete and step numbers ordered. See the mdanalysis backend
  feature's context for the pilot benchmark table.
- Feature workspace converted to ICM on 2026-10-04 and moved into the
  `lop_sf_fcc_workspaces` collection as `lop_sf_fcc_orchestrator_workspaces`
  later the same day; the former canonical documents
  `docs/LopSfFcc_parallelization_contract_plan.md` and
  `docs/debug_N_frames.md` are now pointers here.

### Pending

- Atom-assignment integration (Phases 2–6 of the former parallelization
  contract) is superseded by frame-level parallelization; the
  `parallelization` package (`AtomThreadAssignment` et al.) currently has no
  production consumer. Decide in a future plan whether per-atom partitioning
  is still wanted or the package should be folded into a dedicated feature.
- `LopSfFcc` class attributes `md_params_schema_filepath` /
  `md_params_metadata_schema_filepath` are public class-level attributes and
  depend on the `LTAT_TOP_LEVEL` environment variable; a future plan should
  make them private and resolve schema paths from the package instead of the
  environment.

### Not planned

- Order-parameter calculation code in `lop_sf_fcc.py`.
- HDF5 writing in `LopSfFcc.__call__` (writing is owned by
  `LOP_SF_FCC._conclude`).
- Chunked/append-mode runs (Stage 2.4): measured memory is far below
  available RAM for the argon example; `open_for_append()` remains available
  if a larger system requires it.

## Decision Log

- Frame-level parallelization (MDAnalysis `n_workers`) was chosen over the
  originally planned per-atom thread partitioning: MDAnalysis already
  provides split-apply-combine, worker pickling, and result aggregation, so
  Phases 2–6 of the atom-assignment plan were not needed.
- The atom-assignment contract was still completed (Phase 1) and lives in the
  domain-neutral `parallelization` package, not in this module.
- `LTAT_DEBUG_PLOT_FRAMES` stays an environment variable rather than a CLI
  option; only the help epilog documents it.
- The command_line feature owns the parser and `CLILopSfFcc`; this feature
  owns everything from `__call__` inward.

## Current Data Flow

```text
CLILopSfFcc (from command_line feature)
  │
  ▼
LopSfFcc.__call__
  │ _set_attributes
  ├─ parallel_threads ──────────────────────────┐
  ├─ md_params_json ──▶ validate vs schema ──▶ read ──▶ writer metadata
  ├─ simulation_metadata file ──▶ validate + read ──▶ writer metadata
  ├─ load_universe(psf, trajectory, dt)
  │    └─ LTAT_DEBUG_PLOT_FRAMES ──▶ resolved nm_frames
  ├─ lop_sf_fcc_data_writer_factory.build(HDF5 value object)
  └─ LOP_SF_FCC(atoms, edge_length, cutoff, data_writer)
  │
  ▼
_backend_run_arguments(parallel_threads)
  │  1 → {"backend": "serial"}; N>1 → {"backend": "multiprocessing", n_workers: N}
  ▼
LOP_SF_FCC.run(stop=nm_frames, **run_kwargs)     (timed by LoopTimer)
  │
  ▼
LOP_SF_FCC._conclude ──▶ HDF5 writer (owned by backend feature)
```

## Maintenance Rule

Any change to the orchestration contract (`__call__` data flow, backend
selection, frame limiting, schema validation, or builder wiring) requires, in
the same change:

1. Updated focused tests (`tests/test_lop_sf_fcc_end_to_end.py` and/or
   `tests/test_lop_sf_fcc.py`).
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every cross-feature workspace listed in `README.md`
   (command_line, lop_sf_fcc_mdanalysis, builder_design_pattern).
