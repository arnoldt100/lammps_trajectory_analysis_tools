# Top Level Plan - LOP SF FCC HDF5 Writer

This is the canonical standing plan for the LOP SF FCC HDF5 writer feature
(the concrete HDF5 trajectory data writer and the value-semantics stack that
owns it). It inherits all project-wide rules from
[../../../top_level_plan.md](../../../top_level_plan.md) and the collection
rules from [../top_level_plan.md](../top_level_plan.md), and adds
feature-specific rules; it must not weaken either level.

## Objective

Maintain the HDF5 writer for molecular dynamics trajectories carrying the
per-atom FCC local order parameter structure factor: a concrete
`HDF5LopSfFccTrajectoryDataWriter` satisfying the backend-neutral
[Data Writer Contract Plan](../../../../docs/data_writer_contract_plan.md)
(with one documented divergence — `create()` refuses to overwrite), owned by
value-semantics objects built exclusively through the builder pattern.

Naming follows the repository's `lop_sf_fcc` convention, so class names state
the quantity stored rather than a generic "order parameter".

## Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    lib/
      lop_sf_fcc/
        hdf5_writer/
          __init__.py                                  # registry + exports
          lop_sf_fcc_trajectory_writer_state.py
          lop_sf_fcc_trajectory_writer_behavior.py
          lop_sf_fcc_trajectory_writer_value_object_interface.py
          lop_sf_fcc_trajectory_writer_value_object.py
          lop_sf_fcc_trajectory_writer_builder_keys.py
          lop_sf_fcc_trajectory_writer_builders.py
          hdf5_lop_sf_fcc_trajectory_data_writer.py

tests/
  lib/
    lop_sf_fcc/
      hdf5_writer/          # mirrors the package path
        conftest.py  +  13 test modules
```

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/
  README.md
  context.md
  top_level_plan.md
```

## Design Rules

- **Value semantics:** the writer handle is owned by
  `HDF5LopSfFccTrajectoryWriterValueObject`, which follows the
  `StateValueObjectMutable` template: `__slots__`, `__hash__ = None`,
  defensive copies on state access, copy-on-write `replace()`.
- **Handle exclusion from value identity:** the writer handle stored in
  `LopSfFccTrajectoryWriterState` is excluded from `__eq__` and `__repr__`;
  `replace()` drops the handle; `with_writer()` is the single path attaching
  a live handle; `copy_state` drops it.
- **`update()` blocked while the file is open:** `create()` fixes on-disk
  dataset shapes and root attributes from `layout` and `metadata`; mutating
  either afterward would drift from the file, so `update()` raises
  `DataWriterLifecycleError` when a writer is open. `replace()` stays legal
  (it yields a handle-free object).
- **Metadata sequences are tuples:** `compiler_build_flags` and
  `lmod_modules` are `tuple[str, ...]` so metadata values stay immutable and
  hashable; `as_attributes()` converts them to h5py variable-length strings.
- **All `traj_NNNNN` groups are pre-created** by `create()` with zero-length
  resizable datasets: the file is self-describing before frames arrive;
  writes never create groups; a missing group is a genuine error; empty
  trajectories remain as empty datasets.
- **No overwrite:** `create()` opens with h5py mode `"x"`, never `"w"`. An
  existing target raises `DataWriterTargetError`; callers that want
  replacement must remove the file explicitly. This intentionally diverges
  from the generic `HDF5DataWriter`, which replaces its target.
- **Private state:** every data attribute is private with a single leading
  underscore; state classes expose read-only properties.
- **Backend isolation:** `h5py` imports live only in
  `hdf5_lop_sf_fcc_trajectory_data_writer.py`; the behavior object reaches
  the concrete writer only through the injected registry, so the value
  object stays backend-neutral and test-substitutable.
- **Registry ownership:** `lop_sf_fcc_data_writer_factory` is created and
  populated exactly once in `hdf5_writer/__init__.py`. Implementation modules
  must not register builders at import time. The composite builder receives
  the registry by constructor injection, so tests can substitute a registry
  carrying stub builders.
- **Not `DataWriterProtocol`:** the concrete writer does not implement the
  generic protocol — `write_data(data)`/`append_data(frames)` describe a
  single unnamed stream, whereas every write here is addressed to a
  trajectory index and carries five parallel arrays.

## File Layout (as built)

```text
/                                   (root, holds run metadata as attributes)
|-- attrs: time_step, time_units_label, number_of_trajectories,
|          generation_date, compiler_build_flags, generating_machine,
|          lmod_modules
`-- trajectories/
    `-- traj_NNNNN/
        |-- attrs: trajectory_index
        |-- positions        (n_steps, n_atoms, 3) float64-or-float32
        |-- lop_sf_fcc       (n_steps, n_atoms)    float64-or-float32
        |-- box_lengths      (n_steps, 3)          float64, units attr
        |-- box_angles       (n_steps, 3)          float64, units="degrees"
        `-- step_number      (n_steps,)            int64
```

Group names use the fixed-width form `traj_NNNNN` so lexical ordering matches
trajectory index ordering. The spatial dimension is the fixed module constant
`SPATIAL_DIMENSION = 3`. Simulation time is derived by readers:
`simulation_time = step_number * time_step`; the file stores step numbers
only.

## Writer Contract (as built)

- `create()`: close any prior handle, open mode `"x"`, write root metadata
  attributes, pre-create every `traj_NNNNN` group with zero-length chunked
  resizable datasets (chunk shapes and compression from the layout); `units`
  attributes on `box_lengths`/`box_angles`. Translate
  `FileExistsError`/`OSError`/`TypeError`/`ValueError` to
  `DataWriterTargetError` after closing the partial file.
- `open_for_append()`: open an existing target for appending, keeping stored
  frames and metadata; validates trajectory count and atom count against the
  stored file.
- `write_trajectory(...)`: replace one trajectory's frames with a complete
  validated dataset. Whole-trajectory in memory — small runs and tests only.
- `append_trajectory_frames(...)`: append one frame or a batch to one
  trajectory; validate completely before any resize/assignment (all-or-
  nothing); the first new step must exceed the last stored step.
- `close()`: idempotent; closes the handle and clears it.
- `_validated_frames(...)`: `np.asarray` inputs; promote a single frame to a
  leading axis; require shapes `(n, n_atoms, 3)`, `(n, n_atoms)`, `(n, 3)`,
  `(n, 3)`, `(n,)` with one shared leading `n`; float datasets use
  `same_kind` casting (float32 storage allowed), integer datasets use `safe`
  casting; steps non-negative and strictly increasing; box lengths positive
  and finite; lattice angles in the open interval `(0, 180)` degrees.

### Error contract

| Condition | Exception |
| --- | --- |
| invalid metadata, layout, dtype, shape, rank, index, step ordering, box length, or lattice angle | `DataWriterConfigurationError` |
| write before `create()`, or `update()` while the writer is open | `DataWriterLifecycleError` |
| target already exists, or file cannot be created or opened | `DataWriterTargetError` |

### Data and ordering guarantees

- Frames are stored in input order along the leading axis of each dataset.
- Step numbers are strictly increasing within a trajectory.
- All five datasets in a trajectory group share the same leading dimension.
- Every write is all-or-nothing: validation completes before any resize or
  assignment.
- Trajectory index ordering matches lexical group-name ordering.

## Construction

Every object is instantiated through the builder pattern. Direct constructor
calls from application code are not the supported entry point.

Four products are built, each by a trivial forwarding builder:

| Key constant | Builder | Product |
| --- | --- | --- |
| `LopSfFccRunMetadataBuilderKey` | `LopSfFccRunMetadataBuilder` | `LopSfFccRunMetadata` |
| `LopSfFccTrajectoryLayoutBuilderKey` | `LopSfFccTrajectoryLayoutBuilder` | `LopSfFccTrajectoryLayout` |
| `HDF5LopSfFccTrajectoryDataWriterBuilderKey` | `HDF5LopSfFccTrajectoryDataWriterBuilder` | `HDF5LopSfFccTrajectoryDataWriter` |
| `HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey` | `HDF5LopSfFccTrajectoryWriterValueObjectBuilder` | `HDF5LopSfFccTrajectoryWriterValueObject` |

The composite `HDF5LopSfFccTrajectoryWriterValueObjectBuilder(registry)` is
the entry point: given `file_path` plus metadata and layout arguments (or
pre-built metadata/layout objects, detected with `isinstance`), it builds the
state values through the injected registry, assembles
`LopSfFccTrajectoryWriterState(writer=None)`, constructs the behavior with
the same registry and the writer builder key, and returns the value object.
The writer handle is not built until `create()` (or `open_for_append()`).

### Caller usage

```python
writer_value_object = lop_sf_fcc_data_writer_factory.build(
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    file_path=output_path,
    metadata=run_metadata_arguments,
    layout=layout_arguments,
)

with writer_value_object as writer:
    writer.append_trajectory_frames(...)
```

### Adding another concrete writer

Each concrete writer owns **its own** registry in its owning feature package
(a new `BuilderRegistry` instance with its own keys, builders, and single
registration site), mirroring this package. Registries are never shared
across writers: registration order coupling between otherwise independent
features is hidden global state, which the project-wide plan forbids. A
caller selects a writer by importing that writer's factory and key constants.

## Scale and Performance

Target scale: up to roughly 10,000 frames per trajectory and 500,000 atoms
per frame (one trajectory ≈ 160 GB float64 / 80 GB float32). Consequences:

- **Streaming only at scale:** `append_trajectory_frames` is the supported
  path; `write_trajectory` is reserved for small runs and tests.
- **`float32` is the recommended default** for `position_dtype` and
  `lop_sf_fcc_dtype`; `step_dtype` stays `int64` and `box_dtype` `float64`.
- **Deliberate chunking:** `frames_per_chunk = 1` (appends stay pure writes,
  no read-modify-write) with `atoms_per_chunk = 32768`; `validate()` enforces
  the 64 KiB–8 MiB chunk envelope, waiving the floor when the chunk spans the
  whole atom axis (`n_chunk = min(atoms_per_chunk, number_of_atoms)`).
- **Compression off by default**, expected in production: `gzip` level 4 with
  shuffle for `positions` and `lop_sf_fcc`; a creation property, fixed at
  `create()`.
- **Chunk cache:** the writer opens the file with an `rdcc_nbytes` sized to
  hold several chunks per open dataset.
- **Pre-created groups are cheap:** zero-length chunked datasets allocate no
  raw data.

Deferred: one-file-per-trajectory with external links; MPI/parallel writing
(the design assumes a single writer process holding one handle).

## Test Plan

All tests use pytest with plain asserts; output goes to `tmp_path`. Shared
fixtures in `tests/lib/lop_sf_fcc/hdf5_writer/conftest.py`: valid metadata, a
small layout, a `tmp_path` target, a state, a stub writer, matched frame
arrays.

- `test_lop_sf_fcc_run_metadata.py` — validation, immutability, value
  equality/hashability, h5py attribute round-trip of the tuples.
- `test_lop_sf_fcc_trajectory_layout.py` — validation, chunk-shape
  derivation including `n_chunk = min(atoms_per_chunk, number_of_atoms)`,
  envelope edges, value equality.
- `test_lop_sf_fcc_trajectory_writer_state.py` — delegated validation;
  equality independent of a carried writer (decision test); `repr` excludes
  the writer; `replace` drops the writer and rejects unknown fields;
  `with_writer`; `update` raises.
- `test_lop_sf_fcc_trajectory_writer_value_object_interface.py` — extends
  the template interface, empty `__slots__`, exact abstract member set,
  documented `append_trajectory_frames` signature.
- `test_lop_sf_fcc_trajectory_writer_behavior.py` — structural protocol
  conformance; `copy_state` drops the writer; non-validating `update_state`.
- `test_hdf5_lop_sf_fcc_trajectory_data_writer.py` — lifecycle, file layout,
  metadata attributes, pre-created groups, no-overwrite refusal.
- `test_hdf5_lop_sf_fcc_trajectory_write_validation.py` — the
  `_validated_frames` rules, all-or-nothing writes.
- `test_hdf5_lop_sf_fcc_trajectory_writer_append_mode.py` —
  `open_for_append` keeps frames/metadata, enforces increasing steps,
  rejects missing targets and mismatched trajectory/atom counts.
- `test_hdf5_lop_sf_fcc_trajectory_writer_value_object.py` — value
  semantics, copy-on-write, blocked `update`, context manager.
- `test_lop_sf_fcc_trajectory_writer_builders.py` — the four builders,
  composite build with mappings and pre-built products.
- `test_data_writer_factory.py` — exactly the four documented keys, one
  factory instance, no registration from implementation modules, unknown-key
  and duplicate-registration errors, end-to-end build.
- `test_lop_sf_fcc_trajectory_writer_integration.py` — full write/read-back
  against h5py.
- `test_lop_sf_fcc_trajectory_writer_scale.py` — reduced-scale streaming
  (`slow` marker, excluded from the default run).

## Non-Goals

- No `DataWriterProtocol` implementation (trajectory-indexed five-array
  surface does not fit the single-stream protocol).
- No overwrite mode; no group creation outside `create()`.
- No MPI/parallel writing; no external-link file splitting (deferred).
- No physics or orchestration code in this package.
- Generic writer machinery (protocol, exceptions, `HDF5DataWriter`) stays in
  `data_writer_utils`, governed by the project-wide plan.

## Acceptance Criteria

- `lop_sf_fcc_data_writer_factory.build(...)` yields a usable value object;
  the file layout matches the contract above.
- `create()` refuses an existing target; `open_for_append()` appends after
  stored frames with metadata intact.
- All-or-nothing validation on every write; error contract as documented.
- Focused tests and the full suite pass.

## Migration Log (Completed Work)

### Module relocation into the lop_sf_fcc package — completed 2026-10-05

Converted from `docs/lop_sf_fcc_hdf5_writer_relocation_plan.md`:

- The seven LOP SF FCC writer modules moved from
  `src/lammps_trajectory_analysis_tools/data_writer_utils/` to
  `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/`, file
  names unchanged; only the import paths and qualified references were
  rewritten. Imports of the generic `data_writer_utils.exceptions` stay —
  that is the intended boundary.
- The builder registry moved with the writer and was renamed
  `data_writer_factory` → `lop_sf_fcc_data_writer_factory`; the new
  subpackage `__init__.py` is its single registration site.
  `data_writer_utils` is now registry-free and owns only the generic
  interface (`DataWriterProtocol`, the exception hierarchy,
  `HDF5DataWriter`).
- Consumers rewired: `lop_sf_fcc.py` builds through
  `lop_sf_fcc_data_writer_factory`; `lib/lop_sf_fcc/__init__.py` re-exports
  the registry.
- Tests moved `tests/data_writer_utils/` → `tests/lib/lop_sf_fcc/hdf5_writer/`
  (mirrors the package path); `test_data_writer_factory.py` now targets the
  subpackage; `tests/test_hdf5_data_writer.py` (generic) stayed at the
  tests root unchanged.
- Suite unchanged: 330 passed, 2 skipped.

### Historical: concrete writer sketch superseded

`docs/concrete_lopsf_fcc_data_writer_plan.md` sketched a single-stream HDF5
writer (`LOPSfFCCWriter` with a time scalar per frame). It was superseded by
the value-semantics design: trajectory-indexed groups, `step_number` instead
of a stored time scalar, per-frame box storage, run metadata as root
attributes, and builder-only construction. It is retained as a pointer for
archaeology only.

### Historical: value object design and implementation

The design in `docs/hdf5_lop_sf_fcc_trajectory_writer_value_object_plan.md`
(file layout, state/behavior/value-object split, builder wiring, chunking and
scale rules, error contract) was implemented in `data_writer_utils` and later
extended with `open_for_append()` for chunked multi-`run()` workflows; the
modules were then relocated here (see above). This plan is the canonical
standing contract; the original document is a pointer to this file.

### Historical note

This feature workspace was created on 2026-10-05 inside the
`lop_sf_fcc_workspaces` collection. The original documents at
`docs/hdf5_lop_sf_fcc_trajectory_writer_value_object_plan.md`,
`docs/concrete_lopsf_fcc_data_writer_plan.md`, and
`docs/data_writer_factory_multiple_writers_qa.md` are now pointers here.
