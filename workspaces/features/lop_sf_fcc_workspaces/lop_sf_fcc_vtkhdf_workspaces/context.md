# Context - LOP SF FCC VTKHDF Animation Writer

Status snapshot for the VTKHDF animation writer feature. Update this file
whenever feature behavior, data flow, implementation status, or boundaries
change.

Last reviewed: 2026-10-12.

## Implementation Status

### Done

- Feature workspace and intended production package exist.
- Placeholder modules identify the concrete writer, value object, interface,
  behavior, builders, builder keys, and package registration surface.
- The value-semantics lifecycle and shared concrete animation-writer behavior
  are documented.
- The implementation phases and validation gates are recorded in
  [the implementation plan](../../../../docs/lop_sf_fcc_vtkhdf_animation_writer_plan.md).
- Phase 1 contract and schema are complete:
  - VTKHDF 2.6 temporal `PolyData`;
  - one partition and one vertex per atom at each animation step;
  - direct `h5py` production backend and `vtkHDFReader` interoperability
    oracle;
  - source-adapter conversion boundary;
  - populated contiguous HDF5 group prefix mapped to ordered animation steps;
  - numeric box field data and physical time values;
  - no-overwrite, strict append compatibility, and explicit regeneration
    recovery policy;
  - fixture-based source and expected output trees in `top_level_plan.md`.
- Phase 2 state and behavior are complete:
  - immutable `LopSfFccVtkhdfAnimationMetadata`;
  - immutable `LopSfFccVtkhdfAnimationLayout`;
  - resource-bearing, unhashable
    `LopSfFccVtkhdfAnimationWriterState`;
  - `LopSfFccVtkhdfAnimationWriterValueObjectBehavior` with injected registry
    construction and no concrete backend import;
  - whole-state validation, defensive mappings, replacement, controlled
    update, value equality, writer-free representation, and resource
    exclusion;
  - 44 focused tests passing;
  - Ruff, Ruff format, and mypy passing for Phase 2 files.
- Phase 3 concrete writer is complete:
  - canonical `LopSfFccVtkhdfAnimationWriter` spelling;
  - same-directory staging and hard-link publication without overwrite;
  - explicit abort and exception-safe staging cleanup;
  - complete VTKHDF 2.6 temporal PolyData schema creation;
  - one vertex cell per atom and `lop_sf_fcc` scalar point data;
  - temporal step, point, topology, point-data, and field-data offsets;
  - validation-first single-frame and batch appends;
  - `NSteps` updated last as the append commit marker;
  - strict append compatibility and committed-extent validation;
  - 26 concrete writer tests passing in the normal environment;
  - `vtkHDFReader` interoperability test passing with a temporary optional
    VTK installation;
  - 400 project tests passing, 3 skipped at the Phase 3 gate.
- Phase 4 value object and builders are complete:
  - abstract interface and concrete mutable, unhashable value object;
  - defensive state access and metadata, handle-free replacement, atomic
    controlled update, and state-based equality;
  - create, append-open, frame append, close, abort, and exception-aware
    context management;
  - metadata, layout, concrete-writer, and composite value-object builders
    and keys in their designated modules;
  - exact four-builder package registry populated only in `__init__.py`;
  - stable package exports;
  - 27 focused Phase 4 tests passing, including real create/reopen/append;
  - Ruff and mypy passing;
  - 427 project tests passing, 3 skipped;
  - optional `vtkHDFReader` interoperability test passing.

### Pending

- Implement the HDF5 source adapter and end-to-end conversion entry point.
- Add realistic source-to-VTKHDF conversion tests.
- Wire a consumer only after the writer contract is stable.

### Not Planned

- Computing or modifying LOP SF FCC values.
- Importing MDAnalysis or orchestrator implementation details.
- Exposing a live backend handle as value state.
- Sharing a global registry with the HDF5 writer or unrelated features.
- Treating diagram files as a substitute for an executable contract.

## Decisions

- **Value-oriented wrapper:** the concrete value object follows the mutable
  state/behavior template and is unhashable.
- **Resource excluded from value identity:** equality, representation,
  copying, and replacement ignore and never share the open writer.
- **Mutation blocked while open:** `update()` cannot change schema-defining
  state after target creation; `replace()` remains legal and yields an
  independent handle-free value.
- **Validation before persistence:** every frame or batch is validated
  completely before target datasets are resized or written.
- **Explicit lifecycle:** the shared surface includes `create()`,
  `open_for_append()`, frame append, `close()`, and context management.
- **Feature-owned registry:** the VTKHDF package owns one registry populated
  only by its `__init__.py`; behavior receives it through injection.
- **Backend isolation:** only the concrete writer module imports the selected
  VTKHDF write implementation; the HDF5 source adapter separately owns source
  `h5py` reads.
- **Canonical naming:** public types use `Vtkhdf`; `Vtkhd` is an unimplemented
  scaffold typo.
- **Temporal PolyData 2.6:** atoms are moving PolyData points with one vertex
  cell per atom; `lop_sf_fcc` is the active scalar point-data array.
- **One source group per step:** conversion supports the current producer's
  contiguous populated prefix, requires exactly one frame in each populated
  group, ignores trailing empty pre-created groups, and rejects interior gaps
  or multi-frame groups.
- **Physical time:** `Steps/Values` stores
  `step_number * time_step`; `step_number` is also preserved as temporal
  numeric field data.
- **Box preservation:** source `box_lengths` and `box_angles` are temporal
  three-component field-data arrays. The first release does not synthesize
  box-edge geometry.
- **Backend selection:** direct `h5py` writing avoids a production dependency
  on the VTK Python wheel; `vtkHDFReader` remains required for
  interoperability verification.
- **Recovery:** a VTKHDF file is a derived artifact. Interrupted or
  structurally inconsistent output raises `DataWriterTargetError`; callers
  remove and regenerate it from the source rather than relying on silent
  repair.

## Resolved Phase 1 Questions

1. Dataset type: VTKHDF 2.6 temporal `PolyData`.
2. Temporal unit: one populated source group becomes one animation step with
   one partition.
3. Box data: preserve lengths and angles as field data; visual box edges are
   deferred.
4. Time: store physical time in `Steps/Values` and preserve integer
   `step_number` as field data.
5. Backend: `h5py` for writing; `vtkHDFReader` for interoperability tests.
6. Append: require exact version, type, array schema, dtypes, atom count,
   units, metadata identity, committed dataset extents, and increasing step
   and time values before mutation.

## Planned Data Flow

```text
LOP SF FCC HDF5 source
  | source validation and frame decoding
  v
LopSfFccVtkhdfAnimationWriterValueObject
  | delegates state operations to behavior
  | owns at most one private concrete writer resource
  v
LopSfFccVtkhdfAnimationWriter
  | validates complete batches before mutation
  v
VTKHDF animation target
  | reader-based interoperability verification
  v
VTK-compatible visualization tool
```

## Current Phase

Phases 1 through 4 are complete. Phase 5 source integration remains pending
and must not begin until explicitly requested.

## Maintenance Rule

Any change to the source mapping, VTKHDF schema, lifecycle, validation,
exception behavior, construction, exports, or consumer wiring requires:

1. corresponding focused tests under
   `tests/lib/lop_sf_fcc/vtkhdf_writer/`;
2. an update to `top_level_plan.md` when the standing contract changes;
3. an update to this status snapshot;
4. updates to both workspaces for every new cross-feature dependency;
5. verification against the complete project test suite.