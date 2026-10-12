# LOP SF FCC VTKHDF Animation Writer Implementation Plan

## Purpose

Implement a value-oriented animation writer that converts trajectories
produced by the LOP SF FCC HDF5 writer into a VTKHDF animation suitable for
VTK-compatible visualization tools. The feature owns translation and output
only: it reads persisted trajectory data and never calculates the LOP SF FCC
quantity.

The canonical standing contract is maintained in
[the feature plan](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_vtkhdf_workspaces/top_level_plan.md).
This document records the implementation sequence and verification gates.

## Intended Data Flow

```text
HDF5LopSfFccTrajectoryDataWriter output
  |
  | HDF5LopSfFccAnimationSource adapter
  | validated source metadata, layout, and decoded frame arrays
  v
LopSfFccVtkhdfAnimationWriterValueObject
  |
  | create() / open_for_append() / append_trajectory_frames() / close()
  v
LopSfFccVtkhdfAnimationWriter
  |
  | VTKHDF temporal topology, geometry, point data, and time values
  v
VTKHDF animation file
```

The conversion entry point accepts a source adapter. The concrete HDF5 source
adapter owns source-file reading and emits decoded frame batches; the VTKHDF
writer owns output only and never imports orchestrator or MDAnalysis
implementation details.

## Value-Semantics Design

The implementation follows the repository's behavior-delegation pattern.

### Value object

`LopSfFccVtkhdfAnimationWriterValueObject` owns:

- a private copy of the animation writer state;
- an explicitly supplied, stateless behavior object;
- lifecycle methods that attach and release a concrete writer resource.

The value object provides:

- defensive state access;
- state-based equality and debugging representation;
- copy-on-write `replace(changes)`;
- controlled `update(changes)` while no writer is open;
- `create()`, `open_for_append()`, frame append, and `close()`;
- context-manager lifecycle behavior.

It is mutable, so it is explicitly unhashable. An open writer handle is a
resource rather than value identity: it is excluded from equality and
representation, is dropped by state copying and replacement, and is never
shared between value objects.

### State

A dedicated state type will contain at least:

- source description or source-adapter configuration;
- output path;
- immutable run metadata;
- immutable animation layout and array schema;
- backend writer configuration;
- an optional private concrete writer resource.

The exact source abstraction and VTKHDF layout fields are finalized during
the schema-design phase. State types validate their complete invariants and
expose read-only properties only.

### Shared behavior

`LopSfFccVtkhdfAnimationWriterValueObjectBehavior` is the single state
operation boundary. It implements:

- `copy_state`;
- `validate_state`;
- `replace_state`;
- `update_state`;
- `states_equal`;
- `state_repr`;
- `hash_state` for state-level policy only;
- construction of the concrete writer through an injected builder registry.

It delegates state-specific operations to the state object rather than
interpreting a universal mapping. It contains no file handle, registry
singleton, or backend-global state.

## Shared Concrete Animation Writer Behavior

All concrete animation writer implementations behind the interface must obey
the same observable contract:

### Configuration and value operations

- `metadata` returns a defensive, read-only view or copy of run provenance.
- `writer_configuration` returns the active concrete writer configuration
  and raises a lifecycle error when no writer is open.
- `replace(changes)` returns an independent, validated, handle-free value.
- `update(changes)` validates the complete replacement state and is rejected
  while a writer is open.

### Lifecycle

- `create()` closes any prior resource, refuses accidental overwrite unless
  an explicit future contract allows it, creates the output target, and
  writes the static VTKHDF structure and metadata.
- `open_for_append()` closes any prior resource, opens an existing compatible
  target, validates its schema against configured state, and returns the
  value object.
- `close()` flushes and releases the resource and is idempotent.
- Entering a closed value object creates its target; entering an already-open
  object leaves that resource open. Exiting always calls `close()`.

### Frame writing

- Frame input is validated completely before any persistent mutation.
- All arrays in a frame or batch have one shared leading frame dimension.
- Positions have spatial dimension three.
- LOP SF FCC values have one value per point.
- Step numbers are non-negative and strictly increasing within an animation
  stream, including across append sessions.
- Box lengths are finite and positive; box angles are finite and in the open
  interval `(0, 180)` degrees.
- Frame ordering and atom ordering are preserved.
- A failed validation leaves the file unchanged.
- Backend exceptions are translated to the repository's writer exception
  categories without hiding the original cause.

The exact method name and whether the public call addresses a trajectory
index or a complete animation stream will be fixed after the source-to-frame
mapping is documented. It must remain compatible across all concrete
animation writers that implement this interface.

## Canonical Naming

The format name is `VTKHDF`; therefore public class names use `Vtkhdf`, for
example:

- `LopSfFccVtkhdfAnimationWriter`;
- `LopSfFccVtkhdfAnimationWriterValueObject`;
- `LopSfFccVtkhdfAnimationWriterValueObjectInterface`;
- `LopSfFccVtkhdfAnimationWriterValueObjectBehavior`.

The current one-line `Vtkhd` scaffolds are misspelled and have no supported
public behavior. They will be renamed before implementation and export.

## Implementation Phases

### Phase 1: Contract and schema

Status: **complete (2026-10-12)**.

1. Selected VTKHDF 2.6 temporal `PolyData` with one partition per step.
2. Defined the mapping from the populated contiguous prefix of HDF5
   trajectory groups to animation steps, points, vertex topology,
   `lop_sf_fcc` point data, numeric box field data, and physical time values.
3. Selected direct `h5py` writing as the production backend; VTK's
   `vtkHDFReader` is the interoperability oracle.
4. Selected a source-adapter conversion boundary. The HDF5 adapter accepts an
   input path; the concrete writer receives decoded frames.
5. Defined no-overwrite creation, exact append compatibility, and
   fail-explicitly/regenerate recovery for interrupted or corrupt targets.

Exit gate: fixture-based examples of the source-to-VTKHDF mapping and
expected file tree are approved in the feature plan. The exit gate is met by
the schema and two-step fixture in
[the standing feature plan](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_vtkhdf_workspaces/top_level_plan.md).

### Phase 2: State and behavior

Status: **complete (2026-10-12)**.

1. Added immutable `LopSfFccVtkhdfAnimationMetadata` and
   `LopSfFccVtkhdfAnimationLayout` values plus resource-bearing
   `LopSfFccVtkhdfAnimationWriterState`.
2. Added whole-state validation, handle-free replacement, controlled update,
   value equality, hashing policy, defensive mappings, and writer-free
   representation.
3. Implemented
   `LopSfFccVtkhdfAnimationWriterValueObjectBehavior` using an injected
   `BuilderRegistry`; it imports neither h5py nor a VTK backend.
4. Added 44 focused tests for metadata/layout/state validation, defensive
   copying, equality, replacement, invalid state, registry forwarding, and
   open-resource update boundaries.

Exit gate: state and behavior tests pass without importing the VTK backend.
Met: 44 focused tests pass; Ruff, Ruff format, and mypy pass for the changed
Phase 2 files.

### Phase 3: Concrete VTKHDF writer

Status: **complete (2026-10-12)**.

1. Implemented staged no-overwrite target creation and the complete VTKHDF
   2.6 temporal PolyData structure.
2. Implemented complete frame/batch validation before persistent mutation.
3. Implemented points, scalar point data, numeric field data, vertex
   topology, temporal offsets, and append commit behavior.
4. Implemented append-time identity, metadata, schema, dtype, chunk,
   committed-extent, offset, unit, and ordering checks.
5. Implemented configuration, lifecycle, and target error translation,
   explicit abort, staging cleanup, and regenerate-on-corruption behavior.

Exit gate: generated files match the expected HDF5 tree and reopen through
the selected VTK-compatible reader. Met: 26 concrete writer tests pass in the
normal environment (the VTK test skips when the optional wheel is absent);
the same interoperability test passes with a temporary VTK installation and
confirms two time values, points, and the `lop_sf_fcc` array.

### Phase 4: Value object and builders

Status: **complete (2026-10-12)**.

1. Implemented the abstract value-object interface with explicit state,
   replacement, update, lifecycle, append, abort, equality, representation,
   and context-manager contracts.
2. Implemented the concrete mutable, unhashable value object with defensive
   state access, handle-free replacement, atomic controlled updates, and
   exception-aware context cleanup.
3. Added four focused builders and four keys for metadata, layout, the
   concrete writer, and the composite value object.
4. Created and populated
   `lop_sf_fcc_vtkhdf_animation_writer_factory` only in
   `vtkhdf_writer/__init__.py`; implementation-module reloads do not mutate
   the registry.
5. Exported the stable state, behavior, writer, value-object, construction,
   and schema surfaces.
6. Added 27 focused tests covering the interface, value semantics, lifecycle,
   builders, exact registry contents, single-site registration, exports, and
   a real create/reopen/append flow.

Exit gate: application code can build and use the writer without directly
constructing implementation types. Met: the package factory builds a usable
value object that creates, closes, reopens, and appends a VTKHDF file; Ruff
and mypy pass; the complete suite reports 427 passed and 3 skipped; and the
optional `vtkHDFReader` interoperability test passes.

### Phase 5: Integration

Status: **complete (2026-10-12)**.

1. Added the state-free `LopSfFccVtkhdfAnimationSourceInterface`, immutable
   `LopSfFccVtkhdfAnimationFrame`, and lifecycle-aware
   `HDF5LopSfFccAnimationSource`.
2. Added `LopSfFccVtkhdfAnimationConverter` and the package-level
   `convert_hdf5_lop_sf_fcc_to_vtkhdf()` entry point.
3. Added source and converter builders and keys in the designated modules,
   expanding the package registry to exactly six builders while preserving
   `vtkhdf_writer/__init__.py` as the only registration site.
4. Added realistic producer-to-VTKHDF tests covering contiguous-prefix
   semantics, trailing empty groups, metadata, dtypes, step order, point
   count, LOP values, box data, physical time, output layout overrides, and
   abort-without-publication failures.
5. Verified converted output directly with `vtkHDFReader`.

Exit gate: end-to-end output is readable and scientifically equivalent to
the source fixture. Met: 113 feature tests pass with two optional skips, and
the converted-output interoperability test passes with a temporary VTK
installation. The complete project suite reports 443 passed and 4 skipped.

## Test Plan

Tests belong under `tests/lib/lop_sf_fcc/vtkhdf_writer/` and cover:

1. interface abstractness and absence of base-class state;
2. state validation and defensive copying;
3. equality, representation, replacement, and controlled update;
4. writer-handle exclusion from value identity;
5. lifecycle errors before creation and during open-state mutation;
6. idempotent close and context-manager cleanup after exceptions;
7. create refusal for an existing target;
8. valid single-frame and multi-frame writes;
9. invalid array rank, shape, dtype, step order, box lengths, and angles;
10. validation-before-mutation atomicity;
11. append compatibility and ordering across reopen;
12. builder forwarding, registry ownership, and duplicate-key behavior;
13. VTKHDF file-tree conformance;
14. reader-based interoperability;
15. realistic HDF5-to-VTKHDF conversion.

Focused tests run first, followed by the complete pytest suite and static
diagnostics for all changed Python files.

## Documentation Work

Implementation changes must keep these documents synchronized:

- [feature README](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_vtkhdf_workspaces/README.md);
- [feature context](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_vtkhdf_workspaces/context.md);
- [feature standing plan](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_vtkhdf_workspaces/top_level_plan.md);
- both sides of every cross-feature dependency;
- package exports and public API documentation.

## Completion Criteria

The feature is complete when:

- the value object, behavior, state, concrete writer, builders, and registry
  satisfy the documented contracts;
- VTKHDF output conforms to the selected supported schema;
- file mutation is validation-first and append ordering is preserved;
- a supported VTK-compatible reader opens the generated animation;
- focused and full tests pass;
- static diagnostics add no errors;
- documentation and package exports match the implementation.
