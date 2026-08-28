# Refactor Plan: Replace `accum_nm_neighbors` with `ArrayAccumulator` (Option A)

## Goal

Replace the internally-allocated `accum_lop_nm_neighbors` (plain
`np.zeros(nm_atoms, dtype=np.int64)`) inside
`calculate_sf_fcc_atom_order_parameter_no_coeffs` with an externally-owned
`ArrayAccumulator`, built once via the registry in `LopSfFcc.__call__`, reset
every trajectory frame, and consumed by both calculation functions as a plain
read-only NumPy view (`.finalize()`).

## Rationale (Option A vs Option B)

At the target scale (tens of thousands of trajectories, ~100,000 atoms each),
the dominant cost is the hot loops in `calculate_sf_fcc_atom_order_parameter_with_coeffs`
(iterates over `nm_atoms`) and `calculate_sf_fcc_atom_order_parameter_no_coeffs`
(iterates over atom pairs x wavevectors), executed per frame across the full
workload. `finalize()` is O(1) (a view, not a copy), so returning it once per
frame is negligible. Indexing a plain `np.ndarray` in the hot loop (Option A)
avoids the extra per-element method-call overhead that passing the
`ArrayAccumulator` object itself into the hot loop (Option B) would add.

## Steps

### Step 1 — `LopSfFcc.__call__`: construct the accumulator once

Location: after `nm_atoms` is computed, before the
`for ts in my_universe.trajectory:` loop.

```python
accumulator_nm_neighbors = array_accumulator_builder_registry.build(
    array_accumulator_builder_key,
    dtype=np.int32,
    capacity=np.int32(nm_atoms),
    initial_value=np.int32(0),
    name="atom_neighbor_accumulator",
)
```

Replace the existing comment block:

```python
# Declare here the mutable array_accumulator the number of neighbors
# of each atom.
```

with a comment reflecting the actual construction (one line, e.g.
`# One accumulator reused and reset every frame.`).

### Step 2 — `LopSfFcc.__call__`: reset per frame and pass in

Inside the `for ts in my_universe.trajectory:` loop, before the call to
`calculate_sf_fcc_atom_order_parameter_no_coeffs`:

```python
accumulator_nm_neighbors.reset()

(accum_lop_terms0, accum_nm_neighbors) = (
    calculate_sf_fcc_atom_order_parameter_no_coeffs(
        my_universe,
        self._wavevectors,
        np.float32(command_line_arguments.cutoff),
        accumulator_nm_neighbors,
    )
)
```

`accum_nm_neighbors` (the returned name, unchanged) will now be the
`.finalize()` view rather than an internally-allocated array — no other
call-site change needed for the `with_coeffs` call that follows.

### Step 3 — `calculate_sf_fcc_atom_order_parameter_no_coeffs`: signature and body

- Add parameter `accumulator_nm_neighbors: ArrayAccumulator` to the signature.
- Remove the line:

  ```python
  accum_lop_nm_neighbors = np.zeros(nm_atoms,dtype=np.int64)
  ```

- Replace:

  ```python
  accum_lop_nm_neighbors[atom_index1] += 1
  accum_lop_nm_neighbors[atom_index2] += 1
  ```

  with:

  ```python
  accumulator_nm_neighbors.accumulate(atom_index1, 1)
  accumulator_nm_neighbors.accumulate(atom_index2, 1)
  ```

- Change the return statement:

  ```python
  return (accum_lop_terms, accumulator_nm_neighbors.finalize())
  ```

- Update the docstring: document the new `accumulator_nm_neighbors` parameter
  (caller-owned, mutated in place, must be reset by the caller before each
  use) and note the second return value is now a read-only view.

### Step 4 — `calculate_sf_fcc_atom_order_parameter_with_coeffs`

No signature or body change required — it already only reads
`accum_lop_nm_neighbors[atom_index]`, which works transparently against the
read-only `.finalize()` view.

### Step 5 — Tests: `tests/test_lop_sf_fcc_Ar4Version0.py`

Update `test_lop_sf_fcc_atom_order_parameter_no_coeffs` to construct a fresh
accumulator and pass it in, matching production usage:

```python
accumulator_nm_neighbors = array_accumulator_builder_registry.build(
    array_accumulator_builder_key,
    dtype=np.int32,
    capacity=np.int32(n_atoms),
    initial_value=np.int32(0),
    name="atom_neighbor_accumulator",
)

(programatic_values, programatic_nm_neighbors) = (
    calculate_sf_fcc_atom_order_parameter_no_coeffs(
        my_test_configuration_universe,
        my_test_configuration.wave_vectors,
        my_test_configuration.cutoff,
        accumulator_nm_neighbors,
    )
)
```

Add the necessary import of `array_accumulator_builder_key` /
`array_accumulator_builder_registry` at the top of the test file.

No change expected to `test_lop_sf_fcc_atom_order_parameter_with_coeffs` since
that call site's signature is untouched.

### Step 6 — Tests: `tests/input_files/Ar4Version0.py`

No change required — its reference/expected data
(`self.accum_lop_nm_neighbors`) and its internal fixture-generation helper are
independent of production code and don't need to adopt `ArrayAccumulator`.

### Step 7 — Validation

1. Run focused tests: `tests/test_lop_sf_fcc_Ar4Version0.py`,
   `tests/test_lop_sf_fcc.py`.
2. Run the full suite.
3. Confirm dtype consistency: accumulator uses `np.int32` (matches
   `Ar4Version0.accum_lop_nm_neighbors` dtype); verify no
   `assert_allclose(..., strict=True)` failures due to dtype mismatch against
   `np.int64`-based expectations.

## Files touched

1. `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc.py`
2. `tests/test_lop_sf_fcc_Ar4Version0.py`
