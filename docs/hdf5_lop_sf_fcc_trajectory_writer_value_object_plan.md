# HDF5 LOP SF FCC Trajectory Writer Value Object Plan

## Objective

Define a concrete HDF5 data writer for molecular dynamics trajectory data
carrying the per-atom FCC local order parameter structure factor (LOP SF FCC),
and the value-semantics objects that own it. The writer satisfies the Data
Writer Contract Plan in `project-top-level/docs/data_writer_contract_plan.md`
and reuses the templates in
`src/lammps_trajectory_analysis_tools/design_patterns_templates/value_semantics/`.

Naming follows the repository's existing `lop_sf_fcc` convention, so the class
names state the quantity stored rather than a generic "order parameter".

The existing `HDF5DataWriter`
(`src/lammps_trajectory_analysis_tools/data_writer_utils/hdf5_data_writer.py`)
is the structural guide for lifecycle, validation, and error translation.

## Core Concepts

- Trajectory: one molecular dynamics run. The number of trajectories in a file
  is fixed at configuration time.

- Frame: one recorded step of a single trajectory. A frame consists of:

  - `positions`: a NumPy array of shape `(n_atoms, 3)`, type `float64`.
  - `lop_sf_fcc`: a NumPy array of shape `(n_atoms,)`, type `float64`, holding
    the scalar FCC local order parameter structure factor for each atom.
  - `box_lengths`: a NumPy array of shape `(3,)`, type `float64`, holding the
    simulation box edge lengths `(a, b, c)` for that step.
  - `box_angles`: a NumPy array of shape `(3,)`, type `float64`, holding the
    lattice angles `(alpha, beta, gamma)` in degrees for that step.
  - `step_number`: a scalar integer, type `int64`.

  Box lengths and angles vary from step to step, so they are stored per frame
  rather than as trajectory or run metadata.

- Simulation time: `simulation_time = step_number * time_units`. The file stores
  step numbers only; time is derived by readers from the `time_units` metadata.

- Run metadata: `time_units`, `time_units_label`, `number_of_trajectories`,
  `generation_date`, `compiler_build_flags`, `generating_machine`, and
  `lmod_modules`.

## File Layout

```text
/                                   (root, holds run metadata as attributes)
|-- attrs: time_units, time_units_label, number_of_trajectories,
|          generation_date, compiler_build_flags, generating_machine,
|          lmod_modules
`-- trajectories/
    |-- traj_00000/
    |   |-- attrs: trajectory_index
    |   |-- positions        (n_steps, n_atoms, 3) float64
    |   |-- lop_sf_fcc       (n_steps, n_atoms)    float64
    |   |-- box_lengths      (n_steps, 3)          float64
    |   |-- box_angles       (n_steps, 3)          float64
    |   `-- step_number      (n_steps,)            int64
    |-- traj_00001/
    `-- ...
```

Group names use the fixed-width form `traj_NNNNN` so that lexical ordering
matches trajectory index ordering. `box_angles` are stored in degrees; the unit
is recorded as the dataset attribute `units = "degrees"`, and `box_lengths`
carries the corresponding `units` attribute taken from the layout.

All simulations are three-dimensional. The spatial dimension is a fixed
module-level constant of 3, not a configurable layout field.

## Proposed Modules

All new modules live under
`src/lammps_trajectory_analysis_tools/data_writer_utils/`.

| Module | Contents |
| --- | --- |
| `lop_sf_fcc_trajectory_writer_value_object_interface.py` | `LopSfFccTrajectoryWriterValueObjectInterface` |
| `lop_sf_fcc_trajectory_writer_state.py` | `LopSfFccRunMetadata`, `LopSfFccTrajectoryLayout`, `LopSfFccTrajectoryWriterState` |
| `lop_sf_fcc_trajectory_writer_behavior.py` | `LopSfFccTrajectoryWriterBehavior` |
| `lop_sf_fcc_trajectory_writer_value_object.py` | `HDF5LopSfFccTrajectoryWriterValueObject` |
| `hdf5_lop_sf_fcc_trajectory_data_writer.py` | `HDF5LopSfFccTrajectoryDataWriter` |
| `lop_sf_fcc_trajectory_writer_builder_keys.py` | builder key constants |
| `lop_sf_fcc_trajectory_writer_builders.py` | the four concrete builders |

Existing exceptions in `data_writer_utils/exceptions.py` are reused:
`DataWriterConfigurationError`, `DataWriterLifecycleError`,
`DataWriterTargetError`.

## Value Object Interface

`LopSfFccTrajectoryWriterValueObjectInterface` extends the template
`ValueObjectInterface` and adds the domain surface:

```text
metadata                      -> Mapping[str, Any]   (defensive copy)
writer_configuration          -> Mapping[str, Any]
replace(changes)              -> Self
create()                      -> None
append_trajectory_frames(trajectory_index, step_numbers, positions,
                         lop_sf_fcc_values, box_lengths, box_angles) -> None
close()                       -> None
```

It declares `__slots__ = ()` and stores no instance data, consistent with the
template interface. It also declares the context-manager methods `__enter__`
and `__exit__`, since resource lifetime is part of this contract.

## State Implementation

Three immutable value classes. They are written as ordinary classes with
`__slots__`, private attributes, and read-only properties rather than
dataclasses, to satisfy the repository rule that every data attribute is
private and exposed only through properties.

- `LopSfFccRunMetadata` holds the run provenance fields listed under Core
  Concepts. It provides `as_attributes()` for an h5py-writable mapping and
  `validate()` for field checks.

- `LopSfFccTrajectoryLayout` holds `number_of_atoms`, the dataset dtypes
  `position_dtype`, `lop_sf_fcc_dtype`, `box_dtype` (shared by `box_lengths`
  and `box_angles`), and `step_dtype`, the unit label `length_units_label`, and
  the storage tuning fields `frames_per_chunk` (default 1), `atoms_per_chunk`
  (default 32768), `compression` (default `None`), and `compression_options`
  (default `None`). It provides `validate()` and derives the per-dataset chunk
  shapes, where `n_chunk = min(atoms_per_chunk, number_of_atoms)`:

  - `positions`: `(frames_per_chunk, n_chunk, 3)`
  - `lop_sf_fcc`: `(frames_per_chunk, n_chunk)`
  - `box_lengths`: `(frames_per_chunk, 3)`
  - `box_angles`: `(frames_per_chunk, 3)`
  - `step_number`: `(frames_per_chunk,)`

  Chunking and compression belong to the layout, not to the writer, because
  they are fixed at dataset-creation time and are part of the file's value
  identity. `validate()` requires `frames_per_chunk >= 1` and
  `atoms_per_chunk >= 1`, rejects a `compression_options` value supplied
  without a `compression` filter, and rejects a derived chunk larger than
  roughly 8 MiB. A chunk below the roughly 64 KiB floor is rejected only when
  `atoms_per_chunk < number_of_atoms`, since a chunk that already spans the
  whole atom axis cannot be made larger and small runs must stay valid. See
  Scale and Performance for the sizing rationale.

- `LopSfFccTrajectoryWriterState` holds `file_path`, `metadata`, `layout`, and
  the owned `writer`. It provides `validate_state()`, `replace(changes)`,
  `with_writer(writer)`, and an `update` that raises, since the value is
  immutable. `replace()` accepts only the three value fields and drops the
  writer; `with_writer()` is the single path that attaches a live handle.

### Confirmed design decisions

1. **Handle exclusion from value identity.**
   `LopSfFccTrajectoryWriterState` stores the writer in a private slot that is
   excluded from `__eq__` and `__repr__`. Value identity is therefore
   `(file_path, metadata, layout)`. An open HDF5 handle is a resource, not a
   value, so equality and representation never touch it, and `copy_state`
   drops it. `replace()` returns a state carrying no handle; the new object must
   call `create()` to obtain its own.

2. **`update()` blocked while the file is open.** `create()` fixes on-disk
   dataset shapes and root attributes from `layout` and `metadata`. Mutating
   either afterward would let in-memory state drift from the file, so
   `HDF5LopSfFccTrajectoryWriterValueObject.update()` raises
   `DataWriterLifecycleError` when `state.writer is not None`. `replace()`
   remains legal at all times because it yields a separate, handle-free object.

3. **Metadata sequences are tuples.** `compiler_build_flags` and `lmod_modules`
   are `tuple[str, ...]`. Tuples are immutable and hashable, which keeps the
   metadata a genuine value. `as_attributes()` converts them to h5py
   variable-length string arrays at write time.

4. **All `traj_NNNNN` groups are pre-created.** `create()` builds every group up
   front with zero-length resizable datasets. Consequences:

   - the file is complete and self-describing immediately after `create()`,
     before any frames arrive;
   - write operations never create groups; they look up and resize only, so a
     missing group is a genuine error rather than a first-write condition;
   - `_require_group` range-checks `trajectory_index` against
     `number_of_trajectories` and raises `DataWriterConfigurationError` before
     touching HDF5;
   - trajectories that receive no data remain empty datasets rather than absent
     groups, so readers can iterate `traj_00000 .. traj_(N-1)` uniformly and
     test `shape[0]`;
   - because the layout is fixed at `create()` time, this decision is what makes
     decision 2 necessary.

5. **The writer refuses to overwrite an existing target.** `create()` opens the
   file with h5py mode `"x"`, never `"w"`. If `file_path` already exists, the
   resulting error is translated to `DataWriterTargetError` and no data is
   destroyed. This aligns the writer with the shared Data Writer Contract Plan
   and intentionally diverges from `HDF5DataWriter`, which replaces its target.
   Callers that want replacement must remove the file explicitly.

## Behavior Object

`LopSfFccTrajectoryWriterBehavior` is stateless with respect to trajectory data
and satisfies `StateValueBehaviorProtocol`. It is constructed with the builder
registry and the writer builder key, both injected, so it never imports a
storage backend:

| Method | Behavior |
| --- | --- |
| `copy_state(state)` | return `state.replace({})`, which drops the live handle; the handle is never copied |
| `validate_state(state)` | delegate to `state.validate_state()` |
| `replace_state(state, changes)` | delegate to `state.replace(changes)` |
| `update_state(state, changes)` | return a candidate state; the caller validates before committing |
| `states_equal(left, right)` | value equality, which excludes the handle |
| `state_repr(state)` | `repr(state)` |
| `hash_state(state)` | raise `TypeError`; mutable writer state is unhashable |
| `dummy_method(...)` | template placeholder, returns `None` |
| `build_writer(state)` | build `HDF5LopSfFccTrajectoryDataWriter` through the injected registry from `file_path`, `metadata`, `layout` |
| `create(state)` | build and create the writer, returning the state that carries the handle |

## Value Object

`HDF5LopSfFccTrajectoryWriterValueObject` mirrors the template
`StateValueObjectMutable`:

- `__slots__ = ("_behavior", "_state_implementations")` and `__hash__ = None`.
- `__init__` copies the incoming state, validates it, then stores it.
- `state_implementations` and `state` return defensive copies.
- `metadata` returns `state.metadata.as_attributes()`.
- `writer_configuration` delegates to the owned writer, requiring an open
  writer.
- `replace(changes)` performs copy-on-write and yields a handle-free object.
- `update(changes)` enforces decision 2, then validates before committing.
- `create`, `append_trajectory_frames`, and `close` delegate to the owned
  writer; `_require_writer()` raises `DataWriterLifecycleError` when the writer
  has not been created. `create()` closes any writer it already owns first, so
  the object never leaks a handle.
- `__enter__` calls `create()`; `__exit__` calls `close()`.

## Construction

Every object in this design is instantiated through the builder design pattern
defined in `project-top-level/docs/builder_design_pattern_plan.md`, using the
shared template in
`src/lammps_trajectory_analysis_tools/design_patterns_templates/builder/`.
Direct constructor calls from application code are not the supported entry
point.

### Products and builders

A concrete builder is a single-step callable, `builder(*args, **kwargs) ->
Product`, satisfying `SupportsBuild`. Four products are built:

| Key constant | Builder | Product |
| --- | --- | --- |
| `LopSfFccRunMetadataBuilderKey` | `LopSfFccRunMetadataBuilder` | `LopSfFccRunMetadata` |
| `LopSfFccTrajectoryLayoutBuilderKey` | `LopSfFccTrajectoryLayoutBuilder` | `LopSfFccTrajectoryLayout` |
| `HDF5LopSfFccTrajectoryDataWriterBuilderKey` | `HDF5LopSfFccTrajectoryDataWriterBuilder` | `HDF5LopSfFccTrajectoryDataWriter` |
| `HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey` | `HDF5LopSfFccTrajectoryWriterValueObjectBuilder` | `HDF5LopSfFccTrajectoryWriterValueObject` |

Each builder forwards its arguments to the product constructor and adds no
behavior beyond assembly. Validation stays in the product's `validate()` or
`validate_state()`, so an invalid configuration fails identically whether the
product is built or constructed directly.

### Composite build

`HDF5LopSfFccTrajectoryWriterValueObjectBuilder` is the composite entry point.
Given `file_path` plus metadata and layout arguments, it:

1. builds `LopSfFccRunMetadata` through the registry;
2. builds `LopSfFccTrajectoryLayout` through the registry;
3. assembles a `LopSfFccTrajectoryWriterState` with `writer=None`;
4. returns `HDF5LopSfFccTrajectoryWriterValueObject(state, behavior)`.

It accepts an already-built metadata or layout object in place of the
corresponding arguments, so callers can reuse one metadata value across several
writers. A pre-built product is detected with `isinstance` and passed through
unchanged; anything else is treated as a mapping of constructor arguments and
built through the registry.

The composite builder also constructs the `LopSfFccTrajectoryWriterBehavior`,
injecting the same registry and the writer builder key, so the value object it
returns can later build its writer without importing a backend.

The writer itself is *not* built at this point. Consistent with decision 1, the
value object holds no handle until `create()` is called; at that moment
`LopSfFccTrajectoryWriterBehavior.build_writer` builds the writer through the
registry under `HDF5LopSfFccTrajectoryDataWriterBuilderKey`. The behavior object
therefore holds a reference to the registry rather than importing the concrete
writer class, which is what keeps the value object backend-neutral.

### Registry ownership

One `BuilderRegistry` instance, `data_writer_factory`, is created and populated
in `data_writer_utils/__init__.py` and exported from the package. Registration
happens exactly once, at that single site. Implementation modules must not
register their own builders at import time; the duplicate module-level
registration problem recorded in the builder plan's timer migration must not be
reproduced here.

```python
data_writer_factory: BuilderRegistry[Any] = BuilderRegistry()
data_writer_factory.register_builder(
    LopSfFccRunMetadataBuilderKey, LopSfFccRunMetadataBuilder()
)
data_writer_factory.register_builder(
    LopSfFccTrajectoryLayoutBuilderKey, LopSfFccTrajectoryLayoutBuilder()
)
data_writer_factory.register_builder(
    HDF5LopSfFccTrajectoryDataWriterBuilderKey,
    HDF5LopSfFccTrajectoryDataWriterBuilder(),
)
data_writer_factory.register_builder(
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    HDF5LopSfFccTrajectoryWriterValueObjectBuilder(data_writer_factory),
)
```

The composite builder receives the registry by constructor injection rather
than reaching for a module-level global, so tests can substitute a registry
carrying stub builders.

### Caller usage

```python
writer_value_object = data_writer_factory.build(
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    file_path=output_path,
    metadata=run_metadata_arguments,
    layout=layout_arguments,
)

with writer_value_object as writer:
    writer.append_trajectory_frames(...)
```

Unknown keys raise `BuilderKeyError` and duplicate registration raises
`BuilderRegistrationError`, both from the shared template.

## Concrete Writer

`HDF5LopSfFccTrajectoryDataWriter(file_path, metadata, layout)` validates both
configuration objects in `__init__` and keeps `_file: h5py.File | None`.

Public surface:

```text
configuration                                          -> Mapping[str, Any]
create()                                               -> None
write_trajectory(trajectory_index, step_numbers, positions, lop_sf_fcc_values,
                 box_lengths, box_angles)
append_trajectory_frames(trajectory_index, step_numbers, positions,
                         lop_sf_fcc_values, box_lengths, box_angles)
close()
__enter__() / __exit__()
```

Private helpers: `_write_metadata_attributes`, `_create_trajectory_group`,
`_trajectory_name`, `_require_group`, `_resize_group`, `_validated_frames`,
`_chunk_cache_bytes`, `_require_increasing_from_stored`.

The writer does **not** implement `DataWriterProtocol`. That protocol's
`write_data(data)` and `append_data(frames)` describe a single unnamed stream,
whereas every write here is addressed to a trajectory index and carries five
parallel arrays. Satisfying the protocol would require collapsing that surface
and is not attempted.

### `create()`

Close any prior handle, then open the file with mode `"x"` so that an existing
target is refused rather than replaced. Write the run metadata as root
attributes, create the `trajectories` group, then pre-create one group per
trajectory. Each group gets `positions`, `lop_sf_fcc`, `box_lengths`,
`box_angles`, and `step_number` datasets with leading dimension zero, `maxshape`
leading dimension `None`, and the chunk shape and compression settings derived
from `LopSfFccTrajectoryLayout`. The `units` attributes are written on
`box_lengths` and `box_angles` at creation time.
`FileExistsError`, `OSError`, `TypeError`, and `ValueError` are translated to
`DataWriterTargetError` after closing the partially built file.

### `write_trajectory(...)`

Replace one trajectory's frames with a complete dataset. Validate all five
arrays first, resize the group's datasets to the frame count, then assign.

This method requires the whole trajectory in memory and is therefore only
suitable for small runs. At the target scale it must not be used; see Scale and
Performance.

### `append_trajectory_frames(...)`

Append one frame or a batch of frames to a single trajectory. Validate
completely before any write, then resize from `old_count` to
`old_count + n` and assign to the tail slice. No partial updates.

### `close()`

Close the handle if open and clear `_file`. Idempotent.

### `_validated_frames(...)`

1. `np.asarray` each input.
2. Promote a single frame to a leading axis of length one.
3. Require `positions` of shape `(n, n_atoms, 3)`, `lop_sf_fcc` of shape
   `(n, n_atoms)`, `box_lengths` of shape `(n, 3)`, `box_angles` of shape
   `(n, 3)`, and `step_number` of shape `(n,)`.
4. Require an identical leading `n` across all five arrays.
5. Require the input dtype to be castable to the configured dtype. Float
   datasets use `same_kind` casting, since `float32` storage is the recommended
   default while analysis output is `float64`; integer datasets use `safe`
   casting, so a float step number is rejected.
6. Require step numbers to be non-negative and strictly increasing. On append,
   the first new step must also exceed the last step already stored.
7. Require every box length to be positive and finite, and every lattice angle
   to lie in the open interval `(0, 180)` degrees.

Any failure raises `DataWriterConfigurationError` before a write occurs.

## Scale and Performance

Target scale is up to roughly 10,000 frames per trajectory and up to roughly
500,000 atoms per frame. This dominates every storage decision.

### Volume estimate

Per frame at 500,000 atoms:

| Dataset | `float64` | `float32` |
| --- | --- | --- |
| `positions` | 12.0 MB | 6.0 MB |
| `lop_sf_fcc` | 4.0 MB | 2.0 MB |
| box datasets | 48 B | negligible |

At 10,000 frames one trajectory is about 160 GB in `float64` and about 80 GB in
`float32`. A file holding several trajectories reaches the terabyte range.

### Consequences for this design

- **Streaming only.** `append_trajectory_frames` is the supported path at scale.
  `write_trajectory` would require the full array resident in memory and is
  reserved for small runs and tests.

- **`float32` is the recommended default** for `position_dtype` and
  `lop_sf_fcc_dtype`, halving volume at precision that is adequate for stored
  analysis output. `step_dtype` stays `int64` and `box_dtype` stays `float64`,
  since both are negligible in size. The dtypes remain layout fields, so callers
  who need full precision can opt in.

- **Chunks must be sized deliberately.** A whole frame of `positions` is 6 to
  12 MB, which is too coarse for a single chunk, so `atoms_per_chunk` splits the
  atom axis. The default `frames_per_chunk = 1` with `atoms_per_chunk = 32768`
  gives a `positions` chunk of about 384 KB in `float32`, inside the useful
  range. `validate()` enforces the 64 KiB to 8 MiB envelope.

- **`frames_per_chunk = 1` avoids read-modify-write.** Appending one frame into
  a chunk that spans several frames forces HDF5 to read, decompress,
  recompress, and rewrite the partial chunk on every append. Keeping one frame
  per chunk makes each append a pure write. Raise `frames_per_chunk` only when
  frames are appended in matching batches.

- **Compression is off by default but expected in production.** `gzip` level 4
  with the shuffle filter is the recommended starting point for `positions` and
  `lop_sf_fcc`. It is a per-dataset creation property, so it cannot be changed
  after `create()`.

- **Chunk cache sizing.** The default h5py raw data chunk cache of 1 MB is
  smaller than a single `positions` chunk. The writer should open the file with
  an `rdcc_nbytes` large enough to hold several chunks per open dataset.

- **Pre-created groups stay cheap.** Pre-creating all `traj_NNNNN` groups only
  writes metadata; zero-length chunked datasets allocate no raw data, so
  decision 4 costs nothing at this scale.

- **Append cost is bounded.** Each `append_trajectory_frames` call resizes and
  writes only the tail slice, so cost scales with the appended batch and not
  with the trajectory length already on disk.

### Deferred at this stage

- Whether very large runs should be split into one file per trajectory joined by
  HDF5 external links, rather than a single multi-terabyte file.
- Whether parallel or MPI-backed writing is required; the current design assumes
  a single writer process holding one handle.

## Error Contract

| Condition | Exception |
| --- | --- |
| invalid metadata, layout, dtype, shape, rank, index, step ordering, box length, or lattice angle | `DataWriterConfigurationError` |
| write before `create()`, or `update()` while the writer is open | `DataWriterLifecycleError` |
| target already exists, or file cannot be created or opened | `DataWriterTargetError` |

## Data and Ordering Guarantees

- Frames are stored in input order along the leading axis of each dataset.
- Step numbers are strictly increasing within a trajectory.
- All five datasets in a trajectory group always share the same leading
  dimension, so frame `i` of every dataset refers to the same simulation step.
- Every write is all-or-nothing: validation completes before any resize or
  assignment.
- Trajectory index ordering matches lexical group-name ordering.

## Test Plan

Tests use `pytest` exclusively, with plain `assert` statements and fixtures, per
`.github/instructions/tests.instructions.md`. All file output goes to
`tmp_path`. Existing tests `tests/test_hdf5_data_writer.py` and
`tests/test_accumulator_builder.py` are the style references.

Proposed files:

```text
tests/
  data_writer_utils/
    conftest.py
    test_lop_sf_fcc_run_metadata.py
    test_lop_sf_fcc_trajectory_layout.py
    test_lop_sf_fcc_trajectory_writer_state.py
    test_lop_sf_fcc_trajectory_writer_value_object_interface.py
    test_lop_sf_fcc_trajectory_writer_behavior.py
    test_hdf5_lop_sf_fcc_trajectory_data_writer.py
    test_hdf5_lop_sf_fcc_trajectory_write_validation.py
    test_hdf5_lop_sf_fcc_trajectory_writer_value_object.py
    test_lop_sf_fcc_trajectory_writer_builders.py
    test_data_writer_factory.py
    test_lop_sf_fcc_trajectory_writer_integration.py
    test_lop_sf_fcc_trajectory_writer_scale.py
```

Shared fixtures in `conftest.py`: a valid `LopSfFccRunMetadata`, a small
`LopSfFccTrajectoryLayout` (a handful of atoms, `frames_per_chunk=1`), a
`tmp_path` file target, a state, a stub writer, a created writer, a
`make_frames` factory returning matched `(step_number, positions, lop_sf_fcc,
box_lengths, box_angles)` arrays, and a `write_frames` helper that calls either
write method with the documented argument order.

### 1. `LopSfFccRunMetadata`

1. `validate()` accepts a fully populated, valid metadata value.
2. `validate()` rejects `time_units <= 0`, `number_of_trajectories <= 0`, an
   empty `generating_machine`, an empty `time_units_label`, and a naive
   `generation_date`.
3. `validate()` rejects non-string entries in `compiler_build_flags` or
   `lmod_modules`.
4. Instances reject attribute assignment.
5. Equal field values compare equal; the value is hashable, confirming the
   tuple decision.
6. `as_attributes()` returns every required metadata name, and the flag and
   module tuples round-trip through an h5py attribute write and read as the
   same ordered sequence of strings.

### 2. `LopSfFccTrajectoryLayout`

1. `validate()` accepts a valid layout.
2. `validate()` rejects `number_of_atoms <= 0`, `frames_per_chunk < 1`,
   `atoms_per_chunk < 1`, and an unrecognized dtype string.
3. `validate()` rejects `compression_options` supplied without `compression`.
4. `validate()` rejects a derived chunk above the 8 MiB ceiling, and rejects a
   chunk below the 64 KiB floor only when the atom axis is subdivided.
5. A small layout whose chunk falls below the floor while spanning all atoms is
   still valid, and the default production layout at 500,000 atoms sits inside
   the envelope.
6. Derived chunk shapes are correct for each dataset, including
   `n_chunk = min(atoms_per_chunk, number_of_atoms)` when the atom count is
   smaller than the chunk width.
7. Instances reject attribute assignment and compare by value.

### 3. `LopSfFccTrajectoryWriterState`

1. `validate_state()` delegates to both `metadata.validate()` and
   `layout.validate()`, so an invalid member fails the state.
2. Two states with equal `file_path`, `metadata`, and `layout` compare equal
   **even when one carries a writer and the other does not** — this is the
   direct test of decision 1.
3. `repr()` does not contain the writer.
4. `replace(changes)` applies the change and returns a state whose `writer` is
   `None`, and rejects unknown field names.
5. `with_writer(writer)` returns a state carrying the writer and leaves the
   original untouched.
6. `update(...)` raises, since the value is immutable.

### 4. `LopSfFccTrajectoryWriterValueObjectInterface`

1. The interface extends the template `ValueObjectInterface`.
2. `__slots__` is empty, so the interface stores no instance data.
3. `__abstractmethods__` contains exactly the documented members, including
   those inherited from the template.
4. The interface cannot be instantiated, and neither can a subclass that
   implements only part of the contract.
5. A subclass implementing every member can be instantiated and is recognized
   by `isinstance`.
6. `append_trajectory_frames` declares the documented parameter names in order.

### 5. `LopSfFccTrajectoryWriterBehavior`

1. The behavior implements every `StateValueBehaviorProtocol` member. The
   template protocol is not `runtime_checkable`, so conformance is asserted
   structurally rather than with `isinstance`.
2. `copy_state()` returns an independent, equal state with `writer=None`,
   leaving the source state's writer untouched.
3. `replace_state()` and `update_state()` return new states without mutating
   the input, and `update_state()` deliberately does not validate its
   candidate.
4. `validate_state()` delegates to the state and rejects invalid members.
5. `states_equal()` ignores the writer and `state_repr()` omits it.
6. `hash_state()` raises `TypeError`, and `dummy_method()` returns `None`.
7. `build_writer()` builds through the injected registry: a registry carrying a
   stub builder yields the stub product with the state's file path, metadata,
   and layout forwarded, proving the behavior does not import the concrete
   writer. A registry carrying the real builder yields
   `HDF5LopSfFccTrajectoryDataWriter`.
8. `create()` builds the writer, calls `create()` on it, and returns a state
   carrying it while leaving the input state handle-free.

### 6. `HDF5LopSfFccTrajectoryDataWriter`

1. `configuration` reports the file path, trajectory count, atom count, dtypes,
   chunk shapes, and metadata.
2. The constructor rejects invalid metadata or layout.
3. `create()` produces the documented layout: root attributes, a `trajectories`
   group, and exactly `number_of_trajectories` groups named `traj_NNNNN`.
4. Every pre-created group holds all five datasets with leading dimension zero,
   the expected `maxshape`, the expected chunk shape, and the `units`
   attributes on `box_lengths` and `box_angles` — the test of decision 4.
5. `create()` on an existing path raises `DataWriterTargetError` and leaves the
   original file byte-identical — the test of decision 5.
6. `append_trajectory_frames` accepts a single frame and a batch, preserving
   input order and growing all five datasets together.
7. Appends to different trajectory indices remain independent.
8. `write_trajectory` replaces rather than appends: two successive calls leave
   only the second dataset's contents.
9. Values round-trip exactly for `float64`, and within tolerance when the
   layout specifies `float32`.
10. Writing before `create()` or after `close()` raises
    `DataWriterLifecycleError`.
11. A trajectory index below zero or at or above `number_of_trajectories`
    raises `DataWriterConfigurationError` and does not create a group.
12. `close()` is idempotent and safe when never created.
13. The context manager creates on entry, closes on exit, and closes on an
    exception raised inside the block.
14. Trajectories that receive no data remain readable as empty datasets.

### 7. Validation and atomicity of writes

Parametrized over both `write_trajectory` and `append_trajectory_frames`:

1. Mismatched leading frame counts across the five arrays raise
   `DataWriterConfigurationError`.
2. Wrong shapes raise: `positions` not `(n, n_atoms, 3)`, `lop_sf_fcc` not
   `(n, n_atoms)`, `box_lengths` or `box_angles` not `(n, 3)`.
3. A dtype that cannot be cast raises: a complex array for `positions`, a float
   array for `step_number`. A `float64` input is accepted by `float32` storage.
4. Negative or non-increasing step numbers raise, and on append a step that
   does not follow the last stored step raises while `write_trajectory` may
   restart the sequence.
5. A non-positive box length raises; a lattice angle at or outside `0` or `180`
   degrees raises, including the boundary values.
6. **After any rejected call, the datasets are unchanged in length and
   contents** — the all-or-nothing guarantee.
7. A single frame passed without a leading axis is promoted correctly and
   yields the same file contents as the explicit `(1, ...)` form.

### 8. `HDF5LopSfFccTrajectoryWriterValueObject`

1. The object satisfies its own interface and the `ValueSemantics` protocol.
2. The constructor validates the incoming state and rejects an invalid one.
3. `state_implementations` and `state` return defensive copies that never carry
   the owned writer.
4. `metadata` returns a copy; mutating it does not affect the object.
5. Two value objects built from equal arguments compare equal, and remain equal
   after one of them calls `create()`.
6. `replace(changes)` returns a new object with the change applied, carries no
   handle, and leaves the original object and its open file untouched.
7. `update(changes)` succeeds before `create()`.
8. `update(changes)` raises `DataWriterLifecycleError` while the writer is
   open, and the state is left unmodified — the test of decision 2.
9. `update()` with invalid changes raises and leaves the previous valid state
   in place.
10. `__hash__` is `None` and `hash()` raises.
11. `writer_configuration` and `append_trajectory_frames` before `create()`
    raise `DataWriterLifecycleError`.
12. `close()` releases the handle, is idempotent, and the object stays
    inspectable afterward.
13. The context manager creates, appends, and closes, and the written file
    contains the appended frames.
14. `repr()` omits the owned writer, `dummy_method()` returns `None`, and
    comparison with another type returns `NotImplemented`.

### 9. Builders and registry

1. Each of the four builders satisfies `SupportsBuild`.
2. Each builder forwards its arguments and returns a product equal to the
   directly constructed equivalent.
3. Invalid arguments fail identically whether built or constructed directly,
   confirming validation was not duplicated into the builders.
4. The composite builder returns a value object holding no writer, and rejects
   invalid composed arguments through state validation.
5. The composite builder accepts pre-built metadata and layout objects in place
   of their argument forms, yielding an equal value object and reusing the
   given instance.
6. The composite builder uses its injected registry: a registry with stub
   builders produces stubs, which state validation then rejects.
7. A value object built through the registry opens a usable writer.
8. The package exposes exactly one `data_writer_factory`, and importing the
   implementation modules directly does not register anything further — the
   single-registration-site test.
9. `data_writer_factory.keys()` contains exactly the four documented keys.
10. An unknown key raises `BuilderKeyError`; a duplicate registration raises
    `BuilderRegistrationError` and preserves the original.

### 10. Integration

1. End-to-end: build through the package factory, open with the context
   manager, append several batches to several trajectories, close, then reopen
   with `h5py` and verify every dataset, attribute, unit label, and ordering.
2. Derived simulation time: `step_number * time_units` recomputed from the file
   matches the expected values.
3. A file written with compression reads back identically to an uncompressed
   file written from the same input, and the compression filter is recorded on
   the dataset.
4. A value object that has written one target can `replace()` its file path and
   write a second target, carrying its metadata across.
5. One pre-built metadata value is reused by identity across two value objects
   targeting different files.

### 11. Scale

Marked `slow` and skipped unless `LTAT_RUN_SLOW_TESTS=1` is set, so the default
run stays fast. The marker is registered in the package `conftest.py` rather
than in a global pytest configuration file.

1. A reduced-scale streaming test — 100 frames of 10,000 atoms appended in
   batches of 10, with gzip compression — completes and verifies the stored
   shapes and step numbers, exercising repeated resize-and-append without
   loading the trajectory into memory.
2. Peak allocation measured with `tracemalloc` stays within one batch plus a
   fixed allowance, confirming appends do not accumulate.

Full-scale runs at 10,000 frames and 500,000 atoms are not part of the automated
suite.

## Implementation Order

1. `lop_sf_fcc_trajectory_writer_state.py` with validation.
2. `lop_sf_fcc_trajectory_writer_value_object_interface.py`.
3. `hdf5_lop_sf_fcc_trajectory_data_writer.py`.
4. `lop_sf_fcc_trajectory_writer_behavior.py`.
5. `lop_sf_fcc_trajectory_writer_value_object.py`.
6. `lop_sf_fcc_trajectory_writer_builder_keys.py` and
   `lop_sf_fcc_trajectory_writer_builders.py`.
7. Registry creation and single-site registration in
   `data_writer_utils/__init__.py`.
8. Tests as specified in the Test Plan, written alongside each module rather
   than deferred to the end.

## Non-Goals

- No immutable counterpart value object. Only the mutable
  `HDF5LopSfFccTrajectoryWriterValueObject` is provided, since the object owns a
  file handle whose lifecycle is inherently stateful.
- No target replacement. Overwriting an existing file is out of scope; see
  decision 5.
