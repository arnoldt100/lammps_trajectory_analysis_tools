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
  | validated source metadata, layout, and frame arrays
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

The first implementation may read through a dedicated source adapter or
accept already-decoded frame arrays. That boundary must be selected before
implementation and documented in the feature plan; the animation writer must
not import orchestrator or MDAnalysis implementation details.

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

1. Select and document the supported VTKHDF dataset type and temporal layout.
2. Define the mapping from HDF5 trajectories to animation steps, points,
   topology, point data, box data, and time values.
3. Select the VTKHDF backend dependency and confirm append capabilities.
4. Decide whether the writer accepts an input path, a source adapter, or
   decoded frame batches.
5. Record target overwrite, append-compatibility, and recovery policies.

Exit gate: fixture-based examples of the source-to-VTKHDF mapping and
expected file tree are approved in the feature plan.

### Phase 2: State and behavior

1. Add immutable metadata/layout state and resource-bearing writer state.
2. Add whole-state validation, replacement, controlled update, equality, and
   representation.
3. Implement the behavior object using an injected registry.
4. Add unit tests for copying, equality, replacement, invalid state, and
   open-resource lifecycle boundaries.

Exit gate: state and behavior tests pass without importing the VTK backend.

### Phase 3: Concrete VTKHDF writer

1. Implement target creation and static VTKHDF structure.
2. Implement atomic validation before frame or batch writes.
3. Implement temporal offsets and array append behavior required by the
   selected VTKHDF schema.
4. Implement append-time compatibility checks.
5. Translate configuration, lifecycle, and target failures to the shared
   writer exception hierarchy.

Exit gate: generated files match the expected HDF5 tree and reopen through
the selected VTK-compatible reader.

### Phase 4: Value object and builders

1. Implement the abstract value-object interface.
2. Implement the concrete mutable value object and context manager.
3. Add builder keys and focused builders following the reusable builder
   template.
4. Create and populate the feature registry only in `vtkhdf_writer/__init__.py`.
5. Export only the stable supported surface.

Exit gate: application code can build and use the writer without directly
constructing implementation types.

### Phase 5: Integration

1. Add a conversion entry point in the owning consumer after the writer
   contract is stable.
2. Exercise conversion from a realistic HDF5 LOP SF FCC fixture.
3. Verify animation step order, point count, LOP values, periodic box data,
   and time values in the output.
4. Verify that the generated file opens in at least one supported
   VTK-compatible visualization tool.

Exit gate: end-to-end output is readable and scientifically equivalent to
the source fixture.

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

