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

### Pending

- Correct the placeholder public class spelling from `Vtkhd` to `Vtkhdf`.
- Select the supported VTKHDF dataset type, temporal schema, and backend.
- Specify the exact mapping from the HDF5 source layout to animation steps,
  topology, geometry, point data, box data, and time values.
- Decide whether the public conversion boundary accepts an HDF5 path, a
  source adapter, or decoded frame batches.
- Add state types, behavior, value object, concrete writer, builders, keys,
  registry, and stable package exports.
- Add focused unit, schema-conformance, reader-interoperability, and
  end-to-end conversion tests.
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
  VTKHDF implementation.
- **Canonical naming:** public types use `Vtkhdf`; `Vtkhd` is an unimplemented
  scaffold typo.

## Open Contract Questions

These must be resolved in the schema phase rather than guessed during coding:

1. Which VTKHDF dataset type and temporal organization best represent the
   source trajectories?
2. Does one source trajectory map to one animation, one partition, or another
   explicit unit?
3. How are triclinic box geometry and periodic boundaries represented?
4. Is physical time stored directly, derived from `step_number * time_step`,
   or both?
5. Which backend provides reliable creation, append, and reader-based
   interoperability?
6. What compatibility checks are required before appending to an existing
   file?

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

## Maintenance Rule

Any change to the source mapping, VTKHDF schema, lifecycle, validation,
exception behavior, construction, exports, or consumer wiring requires:

1. corresponding focused tests under
   `tests/lib/lop_sf_fcc/vtkhdf_writer/`;
2. an update to `top_level_plan.md` when the standing contract changes;
3. an update to this status snapshot;
4. updates to both workspaces for every new cross-feature dependency;
5. verification against the complete project test suite.