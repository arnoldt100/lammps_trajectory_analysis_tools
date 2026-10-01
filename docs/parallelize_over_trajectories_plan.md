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
   verification below passes.

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
