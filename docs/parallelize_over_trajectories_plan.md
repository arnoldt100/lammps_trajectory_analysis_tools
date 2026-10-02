# Parallelize Over Trajectories Plan

## Stages

The change is planned in two stages:

1. **Stage 1 — Serial version:** Write a serial version.
2. **Stage 2 — Parallel version:** Convert the serial version to a parallel
   version.

## Stage 1 — Serial Version

### Objective

Make `LOP_SF_FCC` a fully working serial MDAnalysis analysis tool that
calculates the per-atom FCC structure-factor local order parameter for every
frame in a selected range of trajectory frames. The class must follow the
MDAnalysis guidelines for writing new analysis classes, i.e. subclass
`MDAnalysis.analysis.base.AnalysisBase` and implement the
`__init__` / `_prepare` / `_single_frame` / `_conclude` contract.

Target MDAnalysis version: `2.10.0` (from `uv.lock`).

### Target Module

`LOP_SF_FCC` and the copied functions live in
`lib/lop_sf_fcc/lop_sf_fcc_mdanalysis.py`.

### Current State

- `LOP_SF_FCC` subclasses `AnalysisBase` but only appends a dummy value per
  frame and prints the results in `_conclude`.
- `LopSfFcc._set_attributes` creates it via
  `_set_lop_sf_fcc_attribute(self._universe.atoms)` with no physics
  parameters.
- `LopSfFcc.__call__` runs its own explicit frame loop, writes HDF5 output,
  and then calls `self._lop_sf_fcc.run()` with no frame range.

### Functions To Copy Into `lop_sf_fcc_mdanalysis.py`

Copy (not import) from `lop_sf_fcc.py`. Copying avoids a circular import,
because `lop_sf_fcc.py` already imports `lop_sf_fcc_mdanalysis.py`.

| Function | Purpose |
| --- | --- |
| `create_primitive_lattice_vectors` | FCC primitive lattice vectors |
| `create_reciprocal_lattice_vectors` | Reciprocal lattice vectors |
| `create_wavevectors` | The six FCC wavevectors |
| `calculate_lop_fcc_atom_pair_exp_terms` | Sum of `exp(i q·dr)` for one pair |
| `calculate_sf_fcc_atom_order_parameter_no_coeffs` | Per-atom `exp(i q·r)` sums and neighbor counts |
| `calculate_sf_fcc_atom_order_parameter_with_coeffs` | Per-atom normalized order parameter |

Do not copy the unused `calculate_lop_fcc_exp_terms` and
`create_atom_pair_key`.

Required adaptation while copying:

- `calculate_sf_fcc_atom_order_parameter_no_coeffs` takes a `universe` and
  calls `universe.select_atoms("all")`. Change it to take the analysis
  `AtomGroup` so the tool respects the user's selection. Pair indices
  returned by the neighbor search are then local to the `AtomGroup`, so
  accumulators must be sized to `atomgroup.n_atoms`.
- Keep the original functions in `lop_sf_fcc.py` untouched during Stage 1 so
  the existing loop remains a reference implementation.

### `LOP_SF_FCC` Design (MDAnalysis Guidelines)

#### `__init__(self, atomgroup, edge_length, cutoff, **kwargs)`

- Call `super().__init__(atomgroup.universe.trajectory, **kwargs)` so that
  `verbose` and other base-class keywords are forwarded.
- Store `atomgroup`, `edge_length`, and `cutoff` on the instance.
- Compute frame-independent data here: the wavevectors via
  `create_wavevectors(edge_length)`.
- Do not perform any per-frame work or allocate per-frame result arrays.

#### `_prepare(self)`

Called by `run()` after the frame range is resolved, so `self.n_frames`
reflects `start`/`stop`/`step`/`frames`.

- Allocate result arrays on `self.results` (a `Results` object):
  - `self.results.lop_sf_fcc`: `np.zeros((self.n_frames, n_atoms), float64)`.
  - `self.results.box_lengths`: `np.zeros((self.n_frames, 3))`.
  - `self.results.box_angles`: `np.zeros((self.n_frames, 3))`.
- Build the three per-frame accumulators (neighbor counts, raw `exp` terms,
  normalized terms) with `array_accumulator_builder_registry`, sized to
  `n_atoms`.

#### `_single_frame(self)`

- Reset the three accumulators.
- Call the copied `..._no_coeffs` and `..._with_coeffs` functions on
  `self._atomgroup` with the stored wavevectors and cutoff.
- Store into row `self._frame_index` (not `self._ts.frame`):
  `results.lop_sf_fcc`, `results.box_lengths`, `results.box_angles` from
  `self._ts.dimensions`.
- Copy accumulator output into the result arrays; `finalize()` returns
  read-only views that are overwritten next frame.

#### `_conclude(self)`

- Remove the `print`.
- Leave a hook for frame-independent post-processing; nothing is required
  for Stage 1. Frame numbers and times are already available from the base
  class as `self.frames` and `self.times`.

#### Backend Declarations

- `get_supported_backends()` returns `('serial',)`.
- Leave `_analysis_algorithm_is_parallelizable` as `False` (the default).
  Stage 2 will change both and add `_get_aggregator`.

#### Documentation

Write a numpydoc class docstring as recommended by MDAnalysis:
`Parameters` (`atomgroup`, `edge_length`, `cutoff`, `**kwargs`),
`Attributes` (`results.lop_sf_fcc`, `results.box_lengths`,
`results.box_angles`, `frames`, `times`), and a short `Notes` section with
the order-parameter definition. Replace the outdated "dummy integer array"
description.

### Integration With `LopSfFcc`

1. Change `_set_lop_sf_fcc_attribute` to pass `edge_length` and `cutoff`
   from the command-line arguments.
2. In `LopSfFcc.__call__`, call `self._lop_sf_fcc.run(stop=self._nm_frames)`
   so `LTAT_DEBUG_PLOT_FRAMES` is honored.
3. Stage 1 keeps the existing explicit loop and HDF5 writer unchanged. The
   explicit loop is the reference used to verify `LOP_SF_FCC`.
4. Moving the HDF5 writer to read from `self._lop_sf_fcc.results` and
   removing the explicit loop is a follow-up decision, made only after the
   verification below passes. See *Stage 1 Follow-Up — Write HDF5 From
   `LOP_SF_FCC` Results*.

### Tests

Add tests under `tests/`:

- Wavevector helpers in `lop_sf_fcc_mdanalysis.py` match the originals in
  `lop_sf_fcc.py`.
- `results.lop_sf_fcc` shape is `(n_frames, n_atoms)` for full runs and for
  `run(start=..., stop=..., step=...)`.
- On a small trajectory, `results.lop_sf_fcc` matches the existing explicit
  loop frame by frame (`np.allclose`).
- A perfect FCC lattice gives the expected order-parameter value.
- An atom with no neighbors inside the cutoff gives `0.0`.
- An `AtomGroup` subset produces results sized to the subset.

### Stage 1 Phases

1. Copy and adapt the helper functions into `lop_sf_fcc_mdanalysis.py`.
2. Implement `__init__`, `_prepare`, `_single_frame`, `_conclude`, and the
   docstring.
3. Update `_set_lop_sf_fcc_attribute` and the `run()` call in `LopSfFcc`.
4. Add tests and verify equality with the existing explicit loop.

### Stage 1 Exit Criteria

- `LOP_SF_FCC(...).run()` produces per-frame, per-atom results that match
  the existing loop.
- All new and existing tests pass.
- No changes to the HDF5 output format.

**Status:** Phases 1–4 complete. All tests pass, and an end-to-end run on two
frames of `examples/example-lop_sf_fcc-ar_box_small` matches the explicit
loop to about `5e-10`.

### Stage 1 Follow-Up — Write HDF5 From `LOP_SF_FCC` Results (Sketch)

#### Goal

Make `LOP_SF_FCC` the only place the order parameter is calculated.
`LopSfFcc.__call__` calls `run()` and then writes the HDF5 file from
`self._lop_sf_fcc.results`. The explicit frame loop and the three
`LopSfFcc` accumulators are removed.

#### What The Writer Needs Per Frame

`writer.append_trajectory_frames(trajectory_index, step_numbers, positions,
lop_sf_fcc_values, box_lengths, box_angles)` currently receives:

| Argument | Current source (explicit loop) | Source after migration |
| --- | --- | --- |
| `trajectory_index` | loop `counter` | `i`, the row index into `results` |
| `step_numbers` | `ts.frame` | `self._lop_sf_fcc.frames[i]` |
| `positions` | `universe.atoms.positions` | `results.positions[i]` (new) |
| `lop_sf_fcc_values` | `accum_lop_terms1.finalize()` | `results.lop_sf_fcc[i]` |
| `box_lengths` | `ts.dimensions[:3]` | `results.box_lengths[i]` |
| `box_angles` | `ts.dimensions[3:]` | `results.box_angles[i]` |

The only missing data is `positions`.

#### Changes To `LOP_SF_FCC`

- Add `results.positions` with shape `(n_frames, n_atoms, 3)`, dtype
  `float32`, allocated in `_prepare` and filled in `_single_frame` from
  `self._atomgroup.positions`.
- Document the new attribute in the class docstring.
- Do not open or write the HDF5 file inside `_single_frame`. Writing from
  inside a frame would cause side effects in the analysis class and break
  the Stage 2 parallel backends, where frames run in separate workers.

#### Changes To `LopSfFcc.__call__`

This is an intermediate step. See *End State* below.

Sketch:

```python
with self._data_writer as writer:
    self._lop_sf_fcc.run(stop=self._nm_frames)
    results = self._lop_sf_fcc.results
    for i, frame_index in enumerate(self._lop_sf_fcc.frames):
        writer.append_trajectory_frames(i,
                                        frame_index,
                                        results.positions[i],
                                        results.lop_sf_fcc[i],
                                        results.box_lengths[i],
                                        results.box_angles[i])
```

- Remove the explicit `for ts in self._universe.trajectory` loop.
- Remove `_set_accumulator_attributes` and the three accumulator attributes.
- Keep the `LoopTimer`, but time the `run()` call. MDAnalysis also offers
  `run(verbose=True)` for a progress bar.

#### End State — `LopSfFcc.__call__` Only Calls `run()`

Eventually `LopSfFcc.__call__` drops the `with self._data_writer as writer`
context and only does:

```python
self._set_attributes(command_line_arguments)
self._lop_sf_fcc.run(stop=self._nm_frames)
```

The writing moves into `LOP_SF_FCC`:

- `LOP_SF_FCC.__init__` takes the data-writer value object, for example
  `LOP_SF_FCC(atomgroup, edge_length, cutoff, data_writer=..., **kwargs)`.
  `data_writer=None` means "compute only", which keeps the class usable in
  tests and notebooks.
- `_conclude` opens `with self._data_writer as writer:` and appends every
  row of `self.results` using the same loop as the intermediate sketch.
- `_single_frame` still never writes, as stated above.
- `_set_lop_sf_fcc_attribute` passes `self._data_writer` into `LOP_SF_FCC`.
  `LopSfFcc` keeps building the value object, but no longer enters it.

Why `_conclude`:

- It runs once, in the main process, after all frames are done.
- In Stage 2, MDAnalysis runs `_conclude` after the per-worker results are
  aggregated. The same writing code therefore works for the serial and
  parallel backends.
- The file is written in frame order regardless of how frames were split
  across workers.

Resolved: the writer now has an append mode. `open_for_append()` reopens an
existing target made by `create()`, keeps its metadata and stored frames, and
checks that its trajectory groups and datasets match the configured layout.
On the value object it returns `self`, so chunked runs can use:

```python
with self._data_writer as writer:                    # first chunk: create
    ...
with self._data_writer.open_for_append() as writer:  # later chunks: append
    ...
```

The value object's `__enter__` creates the target only when no writer is
open, which is what makes the second form work.

#### Memory Consideration

Storing all positions costs `n_frames × n_atoms × 3 × 4` bytes. For the
argon example this is about `5000 × 5849 × 12 ≈ 350 MB`. If that is too
large, run in chunks:

```python
for start in range(0, nm_frames, chunk_size):
    stop = min(start + chunk_size, nm_frames)
    self._lop_sf_fcc.run(start=start, stop=stop)
    # write rows of this chunk, offsetting trajectory_index by start
```

Chunking keeps memory bounded and fits Stage 2: each chunk can be run with a
parallel backend before its frames are written in order.

#### Tests

- Keep the existing explicit-loop tests in `lop_sf_fcc.py` as the numerical
  reference.
- New test: run `LopSfFcc` on a small trajectory, writing to `tmp_path`, then
  check that every HDF5 dataset matches `LOP_SF_FCC.results`. This includes
  positions, step numbers, and box data.
- Regression test: HDF5 output from the old and new code paths is identical
  for the argon example limited with `LTAT_DEBUG_PLOT_FRAMES`. Capture the
  old output before removing the explicit loop.

#### Phases

1. Add `results.positions` to `LOP_SF_FCC` and its test.
2. Capture reference HDF5 output from the current explicit loop.
3. Replace the explicit loop in `LopSfFcc.__call__` with `run()` plus the
   writer loop. Remove the unused accumulators.
4. Compare the new HDF5 output with the reference and run the full test
   suite.
5. Move the writer into `LOP_SF_FCC._conclude`, pass the data writer
   through `_set_lop_sf_fcc_attribute`, and reduce `LopSfFcc.__call__` to
   `run()` only. Re-run the HDF5 comparison.
6. Optional: add chunked runs if memory profiling requires it, using the
   writer's `open_for_append()` for every chunk after the first.

**Status:** Phases 1–5 complete. Phases 3 and 5 were done together:
`LopSfFcc` went directly to the end state. On three frames of the argon
example, all 25 005 HDF5 datasets match the explicit-loop reference exactly
(maximum absolute difference `0.0`). `LOP_SF_FCC` creates the target on its
first `run()` and calls `open_for_append()` on later runs, so chunked runs
(phase 6) need no further writer changes.

#### Exit Criteria

- `LopSfFcc` produces HDF5 datasets that match the explicit-loop output
  within floating-point tolerance.
- `lop_sf_fcc.py` no longer calculates the order parameter itself.
- `LopSfFcc.__call__` contains no `with self._data_writer` context, only
  `self._lop_sf_fcc.run(...)`.

### Stage 1 Cleanup — Remove Dead Code From `lop_sf_fcc.py` (Sketch)

#### Goal

`LopSfFcc` no longer calculates the order parameter, so the calculation
functions left in `lop_sf_fcc.py` are dead in production code. Remove them so
that `lop_sf_fcc_mdanalysis.py` is the single source of the calculation.
`lop_sf_fcc.py` keeps only `LopSfFcc` and its setup helpers.

#### Dead Code Inventory

Production code does not call any of these. Only tests and test fixtures
import them.

| Symbol in `lop_sf_fcc.py` | Copy in `lop_sf_fcc_mdanalysis.py` | External users |
| --- | --- | --- |
| `create_primitive_lattice_vectors` | yes | `tests/input_files/Ar4Version0.py` |
| `create_reciprocal_lattice_vectors` | yes | `tests/input_files/Ar4Version0.py`, `tests/test_lop_sf_fcc.py` |
| `create_wavevectors` | yes | `tests/test_lop_sf_fcc.py`, `tests/test_lop_sf_fcc_mdanalysis.py` |
| `calculate_lop_fcc_atom_pair_exp_terms` | yes | `tests/test_lop_sf_fcc_Ar4Version0.py` |
| `calculate_sf_fcc_atom_order_parameter_no_coeffs` | yes; takes an `AtomGroup`, not a `Universe` | `tests/test_lop_sf_fcc_Ar4Version0.py`, `tests/test_lop_sf_fcc_mdanalysis.py` |
| `calculate_sf_fcc_atom_order_parameter_with_coeffs` | yes | `tests/test_lop_sf_fcc_Ar4Version0.py`, `tests/test_lop_sf_fcc_mdanalysis.py` |
| `calculate_lop_fcc_exp_terms` | no | `tests/test_lop_sf_fcc_Ar4Version0.py::test_lop_fcc_exp_terms` |
| `create_atom_pair_key` | no | `tests/test_lop_sf_fcc_Ar4Version0.py::test_lop_fcc_exp_terms` |

Imports that become unused once these functions are removed:

- `array_accumulator_builder_key`, `array_accumulator_builder_registry`
- `ArrayAccumulator`
- `calculate_atom_pairs`, `calculate_atom_pairs_vectors`
- `LatticeVectors`, `MDA_Universe`

Keep:

- `key_lop_sf_fcc`, documented as reserved for future use.
- `LoopTimerBuilderKey`, `timer_object_factory`, `load_universe`, and
  `numpy`, which are still used.

The notebooks (`FCC_LOP.ipynb`, `FCC_LOP_1.ipynb`) and `examples/` do not
reference the dead symbols.

#### Decision — Functions Without A Copy

`calculate_lop_fcc_exp_terms` and `create_atom_pair_key` exist only in
`lop_sf_fcc.py`, and only `test_lop_fcc_exp_terms` uses them.

**Decided:** delete both functions and `test_lop_fcc_exp_terms` from
`tests/test_lop_sf_fcc_Ar4Version0.py`.
`test_lop_sf_fcc_atom_order_parameter_no_coeffs` already covers the same
per-atom `exp(iq·r)` sums. Also remove the two names from that test module's
import list.

#### Test Migration

- `tests/input_files/Ar4Version0.py`, `tests/test_lop_sf_fcc.py`, and
  `tests/test_lop_sf_fcc_Ar4Version0.py`: change imports from
  `lop_sf_fcc.lop_sf_fcc` to `lop_sf_fcc.lop_sf_fcc_mdanalysis`.
- `test_lop_sf_fcc_Ar4Version0.py`: pass `universe.atoms` instead of
  `universe` to `calculate_sf_fcc_atom_order_parameter_no_coeffs`.
- `tests/test_lop_sf_fcc_mdanalysis.py`: the reference comparisons
  (`test_wavevectors_match_reference` and
  `test_matches_reference_loop_per_frame`) lose their reference. Replace them
  with the fixed expected values in `Ar4Version0`
  (`atom_accum_exp_terms_with_coeffs`, `wave_vectors`). The perfect-FCC,
  isolated-atom, and HDF5 tests already provide independent checks.
- Run the full test suite before and after. The test count may only drop by
  the removed tests.

#### Phases

1. Delete `test_lop_fcc_exp_terms`, and its imports of
   `calculate_lop_fcc_exp_terms` and `create_atom_pair_key`.
2. Migrate the test and fixture imports to `lop_sf_fcc_mdanalysis.py`, and
   replace the two reference-comparison tests. Run the suite while the old
   functions still exist.
3. Delete the dead functions and their unused imports from `lop_sf_fcc.py`.
   Update the module docstring.
4. Run the full test suite, plus a short `LTAT_DEBUG_PLOT_FRAMES=3` run of the
   argon example compared with `/tmp/ltat_reference.hdf5`.

#### Exit Criteria

- `lop_sf_fcc.py` contains no order-parameter calculation code.
- No module imports calculation functions from `lop_sf_fcc.py`.
- All tests pass, and the HDF5 output is unchanged.

**Status:** Complete.

- Removed the eight dead functions and seven unused imports from
  `lop_sf_fcc.py`.
- Removed `test_lop_fcc_exp_terms` and its `ErrMsgLopFccExpTerms` helper.
- `test_wavevectors_match_reference` and
  `test_matches_reference_loop_per_frame` were replaced by
  `test_wavevectors_match_fixture`, `test_matches_fixture_values`, and
  `test_box_is_stored_per_frame`.
- Results: 311 passed, 2 skipped. The 3-frame argon HDF5 output matches the
  reference exactly (25 005 datasets, maximum absolute difference `0.0`).

## Stage 2 — Parallel Version

### Number Of Workers

The command-line option `--parallel-threads` sets the number of workers for
parallelization.

- Parsed by `positive_integer` in `lop_sf_fcc_cli_parser.py`. The default is
  `1`, and non-positive values are rejected.
- Exposed as `CLILopSfFcc.parallel_threads` and stored in
  `LopSfFcc._parallel_threads`.
- Stage 2 passes this value as the worker count to
  `LOP_SF_FCC.run(...)` (MDAnalysis `n_workers`).

### Objective

Run the per-frame FCC order-parameter calculation in parallel over trajectory
frames, using the MDAnalysis `multiprocessing` backend. Follow the MDAnalysis
"split-apply-combine" guidelines for parallel analysis classes (MDAnalysis
≥ 2.8; this project uses `2.10.0`).

**Scope rule: the HDF5 writer is not parallelized.** Only `_prepare` and
`_single_frame` run in workers. All HDF5 writing stays in `_conclude`, which
MDAnalysis runs once, in the main process, after the worker results are
merged. No worker opens, creates, or writes the HDF5 file.

### How MDAnalysis Runs A Parallel Analysis (2.10.0)

From `MDAnalysis/analysis/base.py`:

1. `run(start, stop, step, frames, n_workers, n_parts, backend, ...)` calls
   `_setup_frames` in the main process, which sets `self.n_frames`.
2. `_setup_computation_groups` splits the selected frames into `n_parts`
   groups. `n_parts` defaults to `n_workers`.
3. The backend calls `self._compute(group)` once per group.
   `BackendMultiprocessing` uses `multiprocessing.Pool.map`, so `self` (the
   analysis object, including its `AtomGroup` and `Universe`) is pickled into
   every worker.
4. Each worker copy runs `_prepare()` and then `_single_frame()` for its own
   frames. `self.n_frames` and `self._frame_index` are local to the group, so
   result arrays are sized per group.
5. In the main process, `frames` and `times` are concatenated with `hstack`,
   and `self.results` is built by `self._get_aggregator().merge(...)`.
6. `_conclude()` runs once in the main process on the merged results.

Environment facts checked for this plan:

- The default multiprocessing start method on this Python (3.14t) is
  `forkserver`, so everything sent to a worker must be picklable.
- `LOP_SF_FCC` on the argon DCD universe pickles successfully.
- The HDF5 writer value object pickles successfully while closed.
- The argon example has 5001 frames and 5849 atoms.
- Target machine: 1 socket, 1 NUMA node, 10 physical cores (CPUs 0–9), and
  1 thread per core (no hyper-threading). The useful worker range is
  therefore `1–10`. The main process mostly waits in `Pool.map`, so all 10
  cores can be workers.

### Stage 2.1 — Make `LOP_SF_FCC` Parallelizable

Changes to `lop_sf_fcc_mdanalysis.py`, following the MDAnalysis guidelines:

- Set `_analysis_algorithm_is_parallelizable = True`.
- `get_supported_backends()` returns `('serial', 'multiprocessing')`. Dask is
  out of scope.
- Implement `_get_aggregator()` to stack every per-frame result along the
  frame axis:

  ```python
  def _get_aggregator(self):
      return ResultsGroup(lookup={
          "lop_sf_fcc": ResultsGroup.ndarray_vstack,
          "box_lengths": ResultsGroup.ndarray_vstack,
          "box_angles": ResultsGroup.ndarray_vstack,
          "positions": ResultsGroup.ndarray_vstack,
      })
  ```

- Keep `_single_frame` free of cross-frame state. It already only uses
  per-group accumulators created in `_prepare` and writes to
  `self.results[...][self._frame_index]`.
- Keep the writer out of workers explicitly. Add `__getstate__` that returns
  a copy of the state with `_data_writer` set to `None`. This means no worker
  can touch the writer and the writer is not pickled. `_conclude` runs on the
  original main-process object, which still holds the writer.
- `_conclude` is unchanged. It writes the merged `self.results` in frame
  order using `self.frames`.
- Update the class docstring: list the supported backends and state that
  writing happens only in the main process.

Tests (`tests/test_lop_sf_fcc_mdanalysis.py`):

- Parametrize the existing shape, value, and frame tests over
  `backend="serial"` and `backend="multiprocessing"` with
  `n_workers ∈ {1, 2, 3}`.
- Multiprocessing results equal serial results exactly for `lop_sf_fcc`,
  `positions`, `box_lengths`, `box_angles`, `frames`, and `times`.
- Results do not depend on `n_parts`. Check `n_parts > n_workers` and
  `n_parts` larger than the number of frames, which gives empty groups.
- With a data writer and `backend="multiprocessing"`, the HDF5 file equals
  the serial-backend file.
- A pickled copy of an analysis object with a writer has
  `_data_writer is None`.
- `run(verbose=True)` with a non-serial backend raises, as documented by
  MDAnalysis. Keep `verbose` for serial only.

### Stage 2.2 — Wire `--parallel-threads` Into `LopSfFcc`

In `LopSfFcc.__call__`:

```python
if self._parallel_threads == 1:
    self._lop_sf_fcc.run(stop=self._nm_frames)
else:
    self._lop_sf_fcc.run(stop=self._nm_frames,
                         backend="multiprocessing",
                         n_workers=self._parallel_threads)
```

- `1` keeps the serial backend, which allows `verbose` progress bars.
- Report the backend and worker count next to the existing
  "Number of trajectory frames" message.
- Update the `--parallel-threads` help text to say it sets the number of
  multiprocessing workers.
- Do not clamp `n_workers` to the frame count. MDAnalysis handles empty
  groups. Cover this with a test (`n_workers > n_frames`).
- Note in the README that each worker uses one process. Users should set
  `OMP_NUM_THREADS=1` to avoid oversubscribing cores through NumPy's threaded
  libraries. On the 10-core target machine, a value above 10 only adds
  overhead. Allow it, but print a warning when `--parallel-threads` exceeds
  `os.cpu_count()`.

Tests: a `LopSfFcc` end-to-end test on a small trajectory with
`parallel_threads ∈ {1, 2}` writing to `tmp_path`. The two HDF5 files must be
equal.

### Stage 2.3 — Verification And Benchmarking

1. **Regression:** run the argon example with `LTAT_DEBUG_PLOT_FRAMES=3` and
   `--parallel-threads` set to 1, 2, and 3. Compare each output with
   `/tmp/ltat_reference.hdf5`; the maximum absolute difference must be `0.0`.
2. **Pilot:** 100 frames with 1, 2, 4, 8, and 10 workers under
   `/usr/bin/time -v`, with `OMP_NUM_THREADS=1`. Record wall time, speed-up,
   and peak memory in this plan. Write output to scratch space, not the
   example directory. With one NUMA node, no CPU pinning or NUMA binding is
   needed.
3. **Full run:** all 5001 frames with the best worker count from the pilot.
   Check that the HDF5 output is complete and that step numbers are in order.

### Stage 2.4 — Memory Control (Conditional)

Do this only if the Stage 2.3 pilot shows peak memory is too high.

- Each worker returns its `positions` and `lop_sf_fcc` arrays to the main
  process through pickling. During the merge, the main process briefly holds
  both the worker copies and the stacked result. For all 5001 frames that is
  about 585 MB of results before this extra copy.
- Run in frame chunks from `LopSfFcc`: call `run(start, stop, backend=...,
  n_workers=...)` once per chunk. `_conclude` creates the HDF5 target on the
  first chunk and uses `open_for_append()` on later chunks, which is already
  implemented. Writing stays serial and in frame order.
- Pick the chunk size so that one chunk's results fit comfortably in memory,
  and keep it a multiple of `n_workers`.

### Stage 2 Exit Criteria

- `LOP_SF_FCC` declares `multiprocessing` support and passes the parallel
  test matrix with results identical to the serial backend.
- `--parallel-threads N` runs `N` multiprocessing workers. `N = 1` runs
  serially.
- HDF5 output is identical across worker counts, and writing happens only in
  the main process.
- Benchmark results (time, speed-up, memory) are recorded in this plan.
