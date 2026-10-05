# LOP SF FCC Orchestrator Feature Workspace

## Feature Goal

Own the `lop_sf_fcc` analysis tool: the `LopSfFcc` orchestrator that turns a
validated command-line configuration into a complete run — loading MD
parameters and metadata, loading the MDAnalysis universe, building the data
writer, selecting the execution backend, timing the run — plus the builder
registry wiring that makes the tool constructible through the shared builder
pattern.

The physics (per-frame FCC structure-factor local order parameter) lives in
the separate `lop_sf_fcc_mdanalysis_workspaces` sibling feature; this feature
owns the orchestration, not the calculation.

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/
  __init__.py             # analysis_tool_builder_registry + subparser_builder_registry
                          # (registration sites; package exports)
  lop_sf_fcc.py           # LopSfFcc orchestrator and its private setup helpers
  lop_sf_fcc_builder.py   # lop_sf_fcc_builder_key, LopSfFccBuilder
```

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/test_lop_sf_fcc_end_to_end.py   # end-to-end runs, backend selection
tests/test_lop_sf_fcc.py              # wavevector/fixture tests (shared with the
                                      # mdanalysis backend feature)
tests/input_files/Ar4Version0.py      # shared Ar4 fixture
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, the as-built orchestration contract,
  test plan, non-goals, acceptance criteria, and the completed migration log.
- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.

Feature-specific logic must not leak into the global scope: orchestration
helpers that exist only for the `lop_sf_fcc` run stay in `lop_sf_fcc.py`;
reusable machinery (assignments, accumulators, writers) stays in its owning
package.

## External Dependencies

- **MDAnalysis integration package** (`integrations/mdanalysis/`):
  `load_universe` for trajectory loading. MDAnalysis imports stay behind
  that integration boundary and the backend feature.
- **Schemas package** (`schemas/`): `validate_json_file`/`read_json_file`
  plus `md_params.schema.json` and `md_metadata.schema.json` for MD
  simulation parameters and metadata.
- **LOP SF FCC HDF5 writer** (`lop_sf_fcc_hdf5_writer_workspaces`, package
  `lib/lop_sf_fcc/hdf5_writer/`): `lop_sf_fcc_data_writer_factory` and
  `HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey` for building the HDF5
  writer value object. See
  [../lop_sf_fcc_hdf5_writer_workspaces/README.md](../lop_sf_fcc_hdf5_writer_workspaces/README.md).
- **Timer utils** (`timer_utils/`): `timer_object_factory` and
  `LoopTimerBuilderKey` for run timing.
- Third-party: NumPy only, in addition to the packages above.

## Cross-Feature Dependencies

Consumers of this feature: none (it is the top of the `lop_sf_fcc` call
chain, reached only through the command_line feature and its own builder
registry).

Dependencies of this feature — each is documented in both workspaces:

- **Command line** (`command_line_workspaces`): this feature consumes
  `CLILopSfFcc` at the `LopSfFcc.__call__` boundary, including
  `parallel_threads` (backend selection) and `md_params_json` (schema
  validation and writer metadata). See
  [../../command_line_workspaces/README.md](../../command_line_workspaces/README.md).
- **LOP SF FCC MDAnalysis backend** (`lop_sf_fcc_mdanalysis_workspaces`):
  `_set_lop_sf_fcc_attribute` constructs `LOP_SF_FCC` and
  `LopSfFcc.__call__` drives it via `run(stop=..., **run_kwargs)`.
  See
  [../lop_sf_fcc_mdanalysis_workspaces/README.md](../lop_sf_fcc_mdanalysis_workspaces/README.md).
- **Builder design pattern template**
  (`design_patterns_workspaces/builder_design_pattern`): the two registries
  owned by `lib/lop_sf_fcc/__init__.py` are `BuilderRegistry` instances;
  `LopSfFccBuilder` satisfies `SupportsBuild`. See
  [../../design_patterns_workspaces/builder_design_pattern/README.md](../../design_patterns_workspaces/builder_design_pattern/README.md).

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Collection rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
- Command-line contract: [../../command_line_workspaces/top_level_plan.md](../../command_line_workspaces/top_level_plan.md)
- MDAnalysis backend contract:
  [../lop_sf_fcc_mdanalysis_workspaces/top_level_plan.md](../lop_sf_fcc_mdanalysis_workspaces/top_level_plan.md)
- HDF5 writer contract:
  [../lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md](../lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md)
