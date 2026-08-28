# Refactor Plan: Replace `accum_lop_terms0` with `accumulator_lop_terms0`

## Goal

Repeat the `accum_nm_neighbors_refactor_plan` (Option A) for the exp(iq·r)
terms accumulator. Replace the internally-allocated `accum_lop_terms`
(plain `np.zeros(nm_atoms, dtype=np.complex64)`) inside
`calculate_sf_fcc_atom_order_parameter_no_coeffs` with an externally-owned
`ArrayAccumulator`, built once via the registry in `LopSfFcc.__call__` as
`accumulator_lop_terms0`, reset every trajectory frame, and consumed by both
calculation functions as a plain read-only NumPy view (`.finalize()`).

## Rationale

Same as the neighbor-count refactor: `finalize()` is O(1) (a view, not a
copy). The hot loop in `calculate_sf_fcc_atom_order_parameter_with_coeffs`
indexes `accum_lop_terms0[atom_index]` per atom across tens of thousands of
frames x ~100,000 atoms, so keeping that consumption on a plain `np.ndarray`
view avoids per-element accumulator method-call overhead in the hot path.

## Steps

### Step 1 — `LopSfFcc.__call__`: construct once, alongside `accumulator_nm_neighbors`

```python
accumulator_lop_terms0 = array_accumulator_builder_registry.build(
    array_accumulator_builder_key,
    dtype=np.complex64,
    capacity=np.int32(nm_atoms),
    initial_value=np.complex64(0.00),
    name="atom_exp_terms_accumulator",
)
```

### Step 2 — reset per frame and pass in

```python
accumulator_nm_neighbors.reset()
accumulator_lop_terms0.reset()
(accum_lop_terms0, accum_nm_neighbors) = (
    calculate_sf_fcc_atom_order_parameter_no_coeffs(
        my_universe,
        self._wavevectors,
        np.float32(command_line_arguments.cutoff),
        accumulator_nm_neighbors,
        accumulator_lop_terms0,
    )
)
```

`accum_lop_terms0` (the returned name) stays as-is — it will now hold the
`.finalize()` view rather than an internally-allocated array, so the
subsequent `with_coeffs` call is unaffected.

### Step 3 — `calculate_sf_fcc_atom_order_parameter_no_coeffs`: signature and body

- Add parameter `accumulator_lop_terms0: ArrayAccumulator`.
- Remove `accum_lop_terms = np.zeros(nm_atoms,dtype=np.complex64)`.
- Replace:

  ```python
  accum_lop_terms[atom_index1] += accum1
  accum_lop_terms[atom_index2] += accum1
  ```

  with:

  ```python
  accumulator_lop_terms0.accumulate(atom_index1, accum1)
  accumulator_lop_terms0.accumulate(atom_index2, accum1)
  ```

- Change the return statement:

  ```python
  return (accumulator_lop_terms0.finalize(), accumulator_nm_neighbors.finalize())
  ```

- Update the docstring: document `accumulator_lop_terms0` as caller-owned,
  mutated in place, reset by the caller before each use.

### Step 4 — `calculate_sf_fcc_atom_order_parameter_with_coeffs`

No change — it already only reads `accum_lop_terms_no_coeffs[atom_index]`,
which works transparently against the read-only `.finalize()` view.

### Step 5 — Tests: `tests/test_lop_sf_fcc_Ar4Version0.py`

Update `test_lop_sf_fcc_atom_order_parameter_no_coeffs` to also construct
`accumulator_lop_terms0` and pass it in, alongside the existing
`accumulator_nm_neighbors`:

```python
accumulator_lop_terms0 = array_accumulator_builder_registry.build(
    array_accumulator_builder_key,
    dtype=np.complex64,
    capacity=np.int32(n_atoms),
    initial_value=np.complex64(0.00),
    name="atom_exp_terms_accumulator",
)

(programatic_values, programatic_nm_neighbors) = (
    calculate_sf_fcc_atom_order_parameter_no_coeffs(
        my_test_configuration_universe,
        my_test_configuration.wave_vectors,
        my_test_configuration.cutoff,
        accumulator_nm_neighbors,
        accumulator_lop_terms0,
    )
)
```

`test_lop_sf_fcc_atom_order_parameter_with_coeffs` remains unaffected.

### Step 6 — `tests/input_files/Ar4Version0.py`

No change required — its reference `accum_lop_terms` computation is
fixture-only and independent of production code.

### Step 7 — Validation

1. Focused: `tests/test_lop_sf_fcc_Ar4Version0.py`.
2. Full suite.
3. Confirm dtype consistency: `np.complex64` (matches existing fixture
   dtype, same as `accumulator_exp_x`).

## Files touched

1. `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc.py`
2. `tests/test_lop_sf_fcc_Ar4Version0.py`
