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

## Package Structure

The canonical import prefix is
`lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer`.
The writer is a sibling of the analysis package under `lib`, with no
old-path compatibility alias. Package exports and builder registration
remain owned by this package's `__init__.py`.

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer/
  __init__.py
  lop_sf_fcc_vtkhdf_animation_converter.py
  lop_sf_fcc_vtkhdf_animation_writer.py
  lop_sf_fcc_vtkhdf_animation_source_interface.py
  hdf5_lop_sf_fcc_animation_source.py
  lop_sf_fcc_vtkhdf_animation_writer_state.py
  lop_sf_fcc_vtkhdf_animation_writer_value_object.py
  lop_sf_fcc_vtkhdf_animation_writer_value_object_interface.py
  lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior.py
  lop_sf_fcc_vtkhdf_animation_writer_builder.py
  lop_sf_fcc_vtkhdf_animation_writer_builder_keys.py

tests/lib/lop_sf_fcc_vtkhdf_writer/
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
  lifecycle operations on supplied writers. It has `__slots__ = ()`, stores
  no data, and neither owns a registry nor constructs writers.
- **Builder construction:** application code builds supported objects through
  concrete builders following the reusable builder pattern. The composite
  builder injects a construction callable into the value object. The callable
  invokes the low-level writer builder registered in the package registry.
  Every create/open operation constructs a fresh writer for current validated
  state; the low-level writer never constructs itself.
- **Registry ownership:** `lop_sf_fcc_vtkhdf_animation_writer_factory` is
  created and populated exactly once in `lop_sf_fcc_vtkhdf_writer/__init__.py`.
  Implementation modules never self-register.
- **Backend isolation:** imports of the chosen VTKHDF implementation live in
  the concrete writer only. Source-side `h5py` reads live in the HDF5 source
  adapter.
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
object preserving the original behavior instance and construction callable.
The callable is a dependency, not value identity, and is excluded from equality,
representation, and persisted metadata. `update(changes)` mutates
only a closed object after validating the complete state.

Direct construction now takes `(state, behavior, writer_builder)`, where
`writer_builder` accepts a `LopSfFccVtkhdfAnimationWriterState` and returns
an unopened concrete writer. Behavior construction takes no arguments;
its `create(state, writer)` and `open_for_append(state, writer)` operations
receive an already constructed writer. The former behavior construction
arguments, key property, and `build_writer()` operation are removed.
The package factory entry points and six registered builder keys are unchanged.
Construction remains lazy: closed value objects and replacements do not
construct a writer or open a file. Valid closed-state updates are applied
before the next writer construction. A writer is attached only after successful
creation/opening; construction and lifecycle errors propagate and leave the
value object closed.

## Shared Animation Writer Contract

### Inspection

- `state_implementations` and `state` return defensive copies.
- `metadata` returns defensive run provenance.
- `writer_configuration` returns active concrete configuration and raises
  `DataWriterLifecycleError` when the writer is closed.

### Lifecycle

- `create()` closes a prior resource, refuses existing final or staging
  targets, creates a same-directory staging file, writes static
  metadata/schema, and leaves the staged writer open.
- `open_for_append()` closes a prior resource, opens an existing target,
  validates schema and metadata compatibility, and returns `self`.
- `close()` flushes, closes, and publishes staged output with a no-overwrite
  hard link; append targets are simply finalized. It is idempotent.
- `abort()` closes without publication and removes only a staging target
  owned by this writer.
- `__enter__()` creates only when closed and returns `self`.
- `__exit__()` publishes on success and aborts staged creation when the body
  raises.

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

### Specification basis

The first implementation targets
[VTKHDF 2.6](https://docs.vtk.org/en/latest/vtk_file_formats/vtkhdf_file_format/vtkhdf_changelog.html)
temporal `PolyData`. Version 2.0 introduced temporal PolyData and version 2.6
added dataset attribute specification, which is used to mark
`lop_sf_fcc` as the scalar point-data array.

The schema follows the official
[VTKHDF format specification](https://docs.vtk.org/en/latest/vtk_file_formats/vtkhdf_file_format/vtkhdf_specifications.html).
VTK's implementation-status documentation reports both temporal data and
`vtkPolyData` reader/writer support. Direct reader interoperability, not a
single visualization application's behavior, is the acceptance oracle.

### Conversion boundary

The public conversion operation receives a
`LopSfFccVtkhdfAnimationSourceInterface`. The concrete
`HDF5LopSfFccAnimationSource` accepts a source path, validates the HDF5
contract, and emits decoded immutable frame values. The concrete VTKHDF
writer receives frames and owns no source-file reading.

This split allows source-reader tests without a VTKHDF target and writer
tests without an HDF5 source. It also prevents source layout logic from
entering shared concrete animation-writer behavior.

### Source group semantics

The current producer pre-creates `number_of_trajectories` groups and writes
one analyzed frame to each group in increasing group-index order. For this
conversion contract:

- populated groups must form a contiguous prefix starting at `traj_00000`;
- every populated group must contain exactly one frame in all five datasets;
- trailing pre-created groups with zero frames are ignored;
- an empty group followed by a populated group is an invalid interior gap;
- a group containing more than one frame is unsupported and rejected;
- source `step_number` values must be strictly increasing across the prefix;
- every frame must have the configured fixed atom count and source dtypes.

Consequently, one populated source group maps to one VTKHDF animation step
and one VTKHDF partition. `Steps/NSteps` is the populated-prefix length, not
the source metadata's pre-created group capacity.

### Selected VTKHDF representation

- `Type`: `PolyData`.
- `Version`: integer pair `[2, 6]`.
- One partition per time step.
- Every atom is a point and one vertex cell, so point-only molecular data
  renders without synthesizing bonds.
- Point order is the source atom-array order and is preserved at every step.
- No stable global atom identifier is invented; point index is the only
  identity available from the source.
- `lop_sf_fcc` is a one-component `PointData` array with HDF5 attribute
  `Attribute = "Scalars"`.
- `step_number`, `box_lengths`, and `box_angles` are temporal numeric
  `FieldData` arrays.
- `Steps/Values` stores physical time as
  `float64(step_number) * float64(time_step)`.
- Length and time unit labels and run provenance are copied to the custom
  top-level `/LOPSFFCC` metadata group. The VTKHDF specification permits
  metadata outside `/VTKHDF` and VTK readers ignore it.
- Box lengths and angles are preserved, including triclinic angles, but the
  first release does not generate visible box-edge geometry or periodic
  images.

### Canonical file tree

```text
/
|-- LOPSFFCC/                              # project metadata; outside VTK model
|   `-- attrs:
|       source_format, time_step, time_units_label, length_units_label,
|       generation_date, compiler_build_flags, generating_machine,
|       lmod_modules
`-- VTKHDF/
    |-- attrs:
    |   Type = "PolyData"
    |   Version = [2, 6]
    |-- NumberOfPoints                     # (NSteps,), all number_of_atoms
    |-- Points                             # (NSteps * number_of_atoms, 3)
    |-- PointData/
    |   `-- lop_sf_fcc                     # (NSteps * number_of_atoms,)
    |       `-- attr: Attribute = "Scalars"
    |-- FieldData/
    |   |-- step_number                    # (NSteps,)
    |   |-- box_lengths                    # (NSteps, 3)
    |   `-- box_angles                     # (NSteps, 3)
    |-- Vertices/
    |   |-- NumberOfCells                  # (NSteps,), all number_of_atoms
    |   |-- NumberOfConnectivityIds        # (NSteps,), all number_of_atoms
    |   |-- Connectivity                   # repeated [0, ..., n_atoms - 1]
    |   `-- Offsets                        # repeated [0, ..., n_atoms]
    |-- Lines/
    |-- Polygons/
    |-- Strips/
    |   # Each empty topology has NumberOfCells and
    |   # NumberOfConnectivityIds containing NSteps zeros,
    |   # empty Connectivity, and one zero Offsets entry per partition.
    `-- Steps/
        |-- attr: NSteps
        |-- Values                         # physical time, float64
        |-- PartOffsets                    # [0, ..., NSteps - 1]
        |-- NumberOfParts                  # all ones
        |-- PointOffsets                   # point-array offsets
        |-- CellOffsets                    # (NSteps, 4)
        |-- ConnectivityIdOffsets          # (NSteps, 4)
        |-- PointDataOffsets/
        |   `-- lop_sf_fcc
        |-- FieldDataOffsets/
        |   |-- step_number
        |   |-- box_lengths
        |   `-- box_angles
        `-- FieldDataSizes/
            |-- step_number                # rows [1 component, 1 tuple]
            |-- box_lengths                # rows [3 components, 1 tuple]
            `-- box_angles                 # rows [3 components, 1 tuple]
```

The topology order in `CellOffsets` and `ConnectivityIdOffsets` is
`Vertices`, `Lines`, `Polygons`, `Strips`, as required by the specification.

### Source-to-target mapping

| Source value | Target value |
| --- | --- |
| group index in contiguous populated prefix | animation-step ordinal |
| `positions[0]` | appended rows in `/VTKHDF/Points` |
| `lop_sf_fcc[0]` | appended rows in `/VTKHDF/PointData/lop_sf_fcc` |
| `step_number[0]` | `/VTKHDF/FieldData/step_number` |
| `step_number[0] * time_step` | `/VTKHDF/Steps/Values` |
| `box_lengths[0]` | `/VTKHDF/FieldData/box_lengths` |
| `box_angles[0]` | `/VTKHDF/FieldData/box_angles` |
| atom-array index | vertex connectivity id |
| run and units metadata | `/LOPSFFCC` attributes |

### Two-step fixture and expected offsets

The Phase 1 contract fixture uses:

```text
source attrs:
  time_step = 0.5
  time_units_label = "ps"
  number_of_trajectories = 2

layout:
  number_of_atoms = 3

traj_00000:
  step_number = [10]
  positions.shape = (1, 3, 3)
  lop_sf_fcc.shape = (1, 3)
  box_lengths = [[10.0, 10.0, 10.0]]
  box_angles = [[90.0, 90.0, 90.0]]

traj_00001:
  step_number = [12]
  positions.shape = (1, 3, 3)
  lop_sf_fcc.shape = (1, 3)
  box_lengths = [[10.5, 10.0, 10.0]]
  box_angles = [[90.0, 90.0, 90.0]]
```

The expected temporal and topology values are:

```text
Steps.NSteps = 2
Steps.Values = [5.0, 6.0]
Steps.PartOffsets = [0, 1]
Steps.NumberOfParts = [1, 1]
Steps.PointOffsets = [0, 3]
Steps.PointDataOffsets/lop_sf_fcc = [0, 3]
Steps.FieldDataOffsets/{step_number,box_lengths,box_angles} = [0, 1]
Steps.CellOffsets = [[0, 0, 0, 0], [3, 0, 0, 0]]
Steps.ConnectivityIdOffsets = [[0, 0, 0, 0], [3, 0, 0, 0]]

NumberOfPoints = [3, 3]
Vertices.NumberOfCells = [3, 3]
Vertices.NumberOfConnectivityIds = [3, 3]
Vertices.Connectivity = [0, 1, 2, 0, 1, 2]
Vertices.Offsets = [0, 1, 2, 3, 0, 1, 2, 3]

Lines|Polygons|Strips.NumberOfCells = [0, 0]
Lines|Polygons|Strips.NumberOfConnectivityIds = [0, 0]
Lines|Polygons|Strips.Connectivity = []
Lines|Polygons|Strips.Offsets = [0, 0]
```

`Points` and `PointData/lop_sf_fcc` contain the two source frames
concatenated in step order. Field-data size rows are `[1, 1]` for
`step_number` and `[3, 1]` for both box arrays.

### Backend decision

Production writing uses the existing `h5py` dependency directly:

- VTKHDF is an HDF5 schema and `h5py` exposes the resizable datasets and
  attributes required by it;
- direct writing supports append without constructing a full in-memory
  `vtkPolyData` for every time step;
- the production package does not gain a large VTK Python-wheel dependency;
- integration verification uses `vtkHDFReader` in a separate test
  environment and checks the observed time steps, points, scalar array, and
  field data.

### Create, append, and recovery policy

- `create()` refuses an existing final target.
- New output is written to a same-directory staging file. Successful
  finalization closes it, creates the final no-overwrite hard link, and then
  removes the staging link.
- Failed creation removes only its known staging file and leaves any existing
  final target untouched.
- `open_for_append()` accepts only a complete final target; staging files are
  never appendable.
- Before append, the writer validates version, type, topology order, dataset
  presence, dtypes, atom count, unit labels, output-defining metadata,
  `NSteps`, every committed extent, and the last stored step/time.
- Input validation completes before any dataset resize.
- An append updates all data and offset datasets first and updates `NSteps`
  last as the commit marker.
- An I/O failure after mutation is reported as `DataWriterTargetError`. On a
  later open, any extent inconsistent with `NSteps` is also a target error.
- There is no silent truncation or repair. VTKHDF is derived from the HDF5
  source, so the supported recovery is to remove the incomplete target and
  regenerate it.

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
- HDF5 animation source adapter;
- animation converter.

The exact product split is finalized with the state model. Builders are
focused forwarding objects; validation remains in products. The composite
value-object builder receives the registry through constructor injection so
tests can supply stub builders without modifying global state.

All feature builders are defined in
`lop_sf_fcc_vtkhdf_animation_writer_builder.py`; all feature builder keys are
defined in `lop_sf_fcc_vtkhdf_animation_writer_builder_keys.py`.
`lop_sf_fcc_vtkhdf_writer/__init__.py` is the only registration site. No product,
behavior, state, or builder module registers itself.

The package registry contains exactly six builders: metadata, layout,
concrete writer, composite value object, HDF5 source, and converter.

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
- Owning command-line or orchestration policy outside this translation
  package.

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

Phases 1 through 5 completed on 2026-10-12.
`LopSfFccVtkhdfAnimationMetadata`, `LopSfFccVtkhdfAnimationLayout`,
`LopSfFccVtkhdfAnimationWriterState`, and
`LopSfFccVtkhdfAnimationWriterValueObjectBehavior` are covered by 44
backend-independent tests. `LopSfFccVtkhdfAnimationWriter` is covered by 26
normal-environment tests plus a passing optional `vtkHDFReader`
interoperability check. The value-object interface, mutable value object,
the original four builders and keys, package registry, single registration
site, and stable exports are covered by 27 focused Phase 4 tests, including a
real create/reopen/append flow. Phase 5 adds the immutable frame contract,
source interface, HDF5 adapter, converter, package-level conversion entry
point, and two corresponding builders and keys. The complete feature suite
reports 113 passed and 2 optional skips; converted output also passes the
`vtkHDFReader` interoperability oracle. The complete project suite reports
443 passed and 4 skipped.