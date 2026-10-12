# Top Level Plan - LOP SF FCC VTKHDF Animation Writer

This is the canonical standing plan for the LOP SF FCC VTKHDF animation
writer. It inherits the project-wide rules from
[../../../top_level_plan.md](../../../top_level_plan.md) and the collection
rules from [../top_level_plan.md](../top_level_plan.md); it must not weaken
either level.

## Objective

Maintain a VTKHDF animation writer that faithfully translates persisted LOP
SF FCC trajectories into a temporal file readable by supported
VTK-compatible visualization tools.

The feature owns:

- the source-to-VTKHDF translation contract;
- animation writer state and value semantics;
- the concrete VTKHDF writer resource;
- builders, keys, registry, and stable exports;
- schema-conformance and interoperability tests.

The detailed delivery sequence is in
[the implementation plan](../../../../docs/lop_sf_fcc_vtkhdf_animation_writer_plan.md).

## Planned Package Structure

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/vtkhdf_writer/
  __init__.py
  lop_sf_fcc_vtkhdf_animation_writer.py
  lop_sf_fcc_vtkhdf_animation_writer_state.py
  lop_sf_fcc_vtkhdf_animation_writer_value_object.py
  lop_sf_fcc_vtkhdf_animation_writer_value_object_interface.py
  lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior.py
  lop_sf_fcc_vtkhdf_animation_writer_builder.py
  lop_sf_fcc_vtkhdf_animation_writer_builder_keys.py

tests/lib/lop_sf_fcc/vtkhdf_writer/
  conftest.py
  test_lop_sf_fcc_vtkhdf_animation_writer.py
  test_lop_sf_fcc_vtkhdf_animation_writer_state.py
  test_lop_sf_fcc_vtkhdf_animation_writer_behavior.py
  test_lop_sf_fcc_vtkhdf_animation_writer_value_object.py
  test_lop_sf_fcc_vtkhdf_animation_writer_builders.py
  test_lop_sf_fcc_vtkhdf_animation_writer_integration.py
```

The package may split schema or source-adapter responsibilities into focused
private modules when implementation evidence requires it. Such modules stay
inside this package and must be added to the README and context.

## Design Rules

- **Canonical naming:** use `Vtkhdf` in public Python class names. `VTKHDF`
  is the format name; the existing `Vtkhd` scaffolds are not public API.
- **Value semantics:** the concrete value object follows the mutable
  state/behavior delegation pattern, returns defensive state copies, supports
  copy-on-write replacement, and is unhashable.
- **Interface-only base:** the value-object interface has `__slots__ = ()`
  and stores no data.
- **Private state:** every data attribute has exactly one leading underscore;
  public access uses properties or explicit methods.
- **Resource exclusion:** a live concrete writer is not value identity. State
  copies and `replace()` drop it; equality and representation ignore it.
- **Controlled mutation:** `update()` validates the complete resulting state
  and raises `DataWriterLifecycleError` while a writer is open.
- **Behavior delegation:** one stateless behavior object owns state copying,
  validation delegation, replacement, update, equality, representation, and
  concrete-writer construction through an injected registry.
- **Builder construction:** application code builds supported objects through
  concrete builders following the reusable builder pattern.
- **Registry ownership:** `lop_sf_fcc_vtkhdf_animation_writer_factory` is
  created and populated exactly once in `vtkhdf_writer/__init__.py`.
  Implementation modules never self-register.
- **Backend isolation:** imports of the chosen VTKHDF implementation live in
  the concrete writer or a focused private adapter module only.
- **Physics isolation:** this package translates existing values and never
  imports or reimplements the LOP SF FCC calculation.
- **Atomic writes:** validation finishes before resizing or assigning any
  persistent dataset.
- **Explicit failures:** backend errors are translated to the shared writer
  exception hierarchy with exception chaining; no broad catches or
  success-shaped fallbacks are permitted.

## Value Identity

Value identity includes configuration that determines observable output:

- output target;
- immutable source description;
- run metadata;
- animation layout and array schema;
- temporal mapping;
- backend writer configuration.

It excludes:

- the open writer handle;
- caches or transient decoded arrays;
- diagnostic counters that do not affect output.

Two values compare equal only when they are the same concrete type and all
identity state compares equal. `replace(changes)` returns a new handle-free
object preserving the original behavior instance. `update(changes)` mutates
only a closed object after validating the complete state.

## Shared Animation Writer Contract

### Inspection

- `state_implementations` and `state` return defensive copies.
- `metadata` returns defensive run provenance.
- `writer_configuration` returns active concrete configuration and raises
  `DataWriterLifecycleError` when the writer is closed.

### Lifecycle

- `create()` closes a prior resource, creates a new target without accidental
  overwrite, writes static metadata/schema, and leaves the writer open.
- `open_for_append()` closes a prior resource, opens an existing target,
  validates schema and metadata compatibility, and returns `self`.
- `close()` flushes, closes, clears the resource, and is idempotent.
- `__enter__()` creates only when closed and returns `self`.
- `__exit__()` always closes, including when the body raises.

### Frame or batch append

The final method signature is established during schema design, but every
implementation must guarantee:

- complete validation before mutation;
- a shared leading frame dimension across parallel arrays;
- positions shaped by three spatial dimensions;
- one LOP SF FCC point value per position;
- finite numeric inputs;
- non-negative, strictly increasing steps within and across append sessions;
- positive box lengths;
- box angles strictly between zero and 180 degrees;
- preserved frame and point ordering;
- no partial resize or assignment after invalid input.

If multiple concrete animation writers implement this interface, they must
provide the same lifecycle, ordering, validation, and error behavior. Format
differences remain behind the concrete writer boundary.

## Source-to-Output Contract

The source is the persisted output contract of the LOP SF FCC HDF5 writer:
positions, per-point `lop_sf_fcc`, box lengths, box angles, step numbers, and
run metadata. The writer must preserve those scientific values exactly,
subject only to an explicitly configured and validated output dtype.

Before production implementation, this plan must be extended with:

- the selected VTKHDF dataset type and version;
- the complete file tree and required attributes;
- the mapping of trajectories to temporal datasets or partitions;
- topology and connectivity representation;
- periodic and triclinic box representation;
- simulation time representation;
- append offsets and compatibility checks.

No implementation should infer these details from a single visualization
tool; the mapping must be backed by the supported VTKHDF specification and
reader-based tests.

## Error Contract

| Condition | Exception |
| --- | --- |
| invalid state, schema, rank, shape, dtype, index, step ordering, box length, box angle, or incompatible append input | `DataWriterConfigurationError` |
| write before create/open, update while open, or access to closed writer configuration | `DataWriterLifecycleError` |
| target exists, cannot be created/opened, is not VTKHDF, or cannot be flushed/closed correctly | `DataWriterTargetError` |

Validation errors occur before target mutation. Backend exceptions retain
their original cause through exception chaining.

## Construction

Common concrete products that implement shared protocols receive builders.
At minimum, the package will define builder keys and builders for:

- state or composite state;
- behavior when configuration is required;
- concrete VTKHDF writer;
- concrete VTKHDF animation writer value object.

The exact product split is finalized with the state model. Builders are
focused forwarding objects; validation remains in products. The composite
value-object builder receives the registry through constructor injection so
tests can supply stub builders without modifying global state.

## Test Plan

Tests verify observable behavior:

1. the interface stores no state and cannot be instantiated;
2. construction copies and validates state;
3. properties do not expose mutable internal storage;
4. equality ignores writer resources but includes output-defining state;
5. replacement is independent and handle-free;
6. update succeeds while closed and fails while open;
7. lifecycle methods and context management release resources reliably;
8. create refuses accidental overwrite;
9. valid frames and batches preserve values and ordering;
10. invalid shapes, dtypes, steps, boxes, and schema are rejected before
    mutation;
11. append validates stored compatibility and cross-session step order;
12. registry construction is deterministic and has one registration site;
13. output conforms to the documented VTKHDF tree;
14. a supported VTK-compatible reader opens the animation and observes the
    expected steps and arrays;
15. a realistic HDF5 source converts without changing scientific values.

Focused tests run before the complete suite. Integration tests that require a
third-party reader remain separate from unit tests.

## Documentation Rules

- Update this plan when the standing contract changes.
- Update `context.md` whenever status, decisions, or data flow changes.
- Update `README.md` whenever boundaries, dependencies, owned modules, or
  consumers change.
- Document cross-feature dependencies in both workspaces.
- Keep the implementation plan aligned with completed phase gates.

## Non-Goals

- Calculating LOP SF FCC values.
- Owning MDAnalysis execution or orchestration.
- Building a general-purpose VTKHDF framework.
- Supporting every VTK dataset type or historical VTK format.
- Hiding source corruption, unsupported schemas, or backend failures.
- Sharing open resources across copied or replaced value objects.
- Adding a consumer before the output contract is stable and tested.

## Acceptance Criteria

- Public naming consistently uses `Vtkhdf`.
- State, behavior, value object, concrete writer, builders, registry, and
  exports follow project conventions.
- Source values, ordering, box data, and temporal information are preserved.
- Output conforms to the documented VTKHDF schema.
- Invalid input cannot partially mutate the target.
- Create, append, close, and context-manager semantics are tested.
- At least one supported VTK-compatible reader opens generated output.
- Focused tests, the complete suite, and static diagnostics pass.
- Feature, dependency, and public API documentation agree with code.

## Current Phase

Planning and contract definition. Production modules remain placeholders;
the schema and backend questions listed in `context.md` are prerequisites for
implementation.