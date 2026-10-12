# LOP SF FCC VTKHDF Animation Writer Feature Workspace

## Feature Goal

Own the VTKHDF animation writer for persisted LOP SF FCC trajectories. The
feature converts the trajectory data produced by
`HDF5LopSfFccTrajectoryDataWriter` into a standards-conforming temporal
VTKHDF file for VTK-compatible visualization tools.

The feature performs translation and output only. It does not calculate
LOP SF FCC values, alter scientific results, or own trajectory analysis.

## Structural Boundaries

Planned production scope:

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/vtkhdf_writer/
  __init__.py
    # lop_sf_fcc_vtkhdf_animation_writer_factory
    # single registration site and stable exports
  lop_sf_fcc_vtkhdf_animation_writer.py
    # LopSfFccVtkhdfAnimationWriter
  lop_sf_fcc_vtkhdf_animation_source_interface.py
    # LopSfFccVtkhdfAnimationSourceInterface
  hdf5_lop_sf_fcc_animation_source.py
    # HDF5LopSfFccAnimationSource
  lop_sf_fcc_vtkhdf_animation_writer_state.py
    # immutable metadata/layout and resource-bearing writer state
  lop_sf_fcc_vtkhdf_animation_writer_value_object.py
    # LopSfFccVtkhdfAnimationWriterValueObject
  lop_sf_fcc_vtkhdf_animation_writer_value_object_interface.py
    # LopSfFccVtkhdfAnimationWriterValueObjectInterface
  lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior.py
    # LopSfFccVtkhdfAnimationWriterValueObjectBehavior
  lop_sf_fcc_vtkhdf_animation_writer_builder.py
    # concrete builders
  lop_sf_fcc_vtkhdf_animation_writer_builder_keys.py
    # concrete builder keys
```

`Vtkhdf` is the canonical class-name spelling. The existing `Vtkhd`
one-line scaffolds are misspelled placeholders and are not a supported API.

Centralized tests will mirror the package:

```text
tests/lib/lop_sf_fcc/vtkhdf_writer/
  conftest.py
  test_lop_sf_fcc_vtkhdf_animation_writer_state.py
  test_lop_sf_fcc_vtkhdf_animation_writer_behavior.py
  test_lop_sf_fcc_vtkhdf_animation_writer.py
  # Planned in later phases:
  test_lop_sf_fcc_vtkhdf_animation_writer_value_object.py
  test_lop_sf_fcc_vtkhdf_animation_writer_builders.py
  test_lop_sf_fcc_vtkhdf_animation_writer_integration.py
```

Tests never live in this feature workspace or under `src`.

Standing documentation in this folder:

- `top_level_plan.md` defines the canonical feature contract, design rules,
  tests, non-goals, and acceptance criteria.
- `context.md` records current implementation status and decisions.
- `uml_diagrams/` contains design aids only; diagrams do not override the
  written contract.

## External Dependencies

- **LOP SF FCC HDF5 writer:** defines the source trajectory layout and
  metadata consumed by this feature.
- **Value-semantics template:** supplies the state/behavior delegation model
  adapted by the writer value object.
- **Builder template:** supplies `BuilderRegistry`, builder protocols, and
  registry errors.
- **Data writer utilities:** supplies the shared configuration, lifecycle,
  and target exception categories.
- **h5py:** selected production backend for direct VTKHDF 2.6 creation and
  append. It is isolated in the concrete writer and HDF5 source-adapter
  modules.
- **VTK `vtkHDFReader`:** interoperability oracle for integration tests; it
  is not part of the production write path.
- **NumPy:** validates and transfers source frame arrays without introducing
  analysis logic.

## Cross-Feature Dependencies

Dependencies of this feature:

- **LOP SF FCC HDF5 writer:** supplies persisted positions, LOP SF FCC point
  values, box geometry, step numbers, and run metadata. See
  [the HDF5 writer workspace](../lop_sf_fcc_hdf5_writer_workspaces/README.md).
- **Value semantics:** defines defensive copying, state equality,
  replacement, controlled mutation, and behavior delegation. See
  [the value-semantics workspace](../../design_patterns_workspaces/value_semantics/README.md).
- **Builder pattern:** defines builder registry ownership and construction.
  See
  [the builder workspace](../../design_patterns_workspaces/builder_design_pattern/README.md).

Consumers of this feature are not yet wired. A command-line or orchestration
consumer may be added only after the source-to-animation mapping and public
writer contract are stable; that dependency must then be documented in both
feature workspaces.

## Related Documents

- Implementation plan:
  [docs/lop_sf_fcc_vtkhdf_animation_writer_plan.md](../../../../docs/lop_sf_fcc_vtkhdf_animation_writer_plan.md)
- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Collection rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
- HDF5 source contract:
  [../lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md](../lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md)
- Value-semantics contract:
  [../../design_patterns_workspaces/value_semantics/top_level_plan.md](../../design_patterns_workspaces/value_semantics/top_level_plan.md)
- Builder contract:
  [../../design_patterns_workspaces/builder_design_pattern/top_level_plan.md](../../design_patterns_workspaces/builder_design_pattern/top_level_plan.md)
