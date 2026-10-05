# LOP SF FCC HDF5 Writer Feature Workspace

## Feature Goal

Own the HDF5 trajectory data writer for the FCC structure-factor local order
parameter: the concrete `HDF5LopSfFccTrajectoryDataWriter`, the value-semantics
stack that owns it (`LopSfFccRunMetadata`, `LopSfFccTrajectoryLayout`,
`LopSfFccTrajectoryWriterState`, `LopSfFccTrajectoryWriterBehavior`,
`HDF5LopSfFccTrajectoryWriterValueObject` and its interface), the four builder
keys and concrete builders, and the `lop_sf_fcc_data_writer_factory` builder
registry with its single registration site.

The writer persists a fixed set of trajectories, each carrying per-frame
`positions`, per-atom `lop_sf_fcc` values, `box_lengths`, `box_angles`, and
`step_number`, plus run provenance as HDF5 root attributes. The writer
satisfies the backend-neutral
[Data Writer Contract Plan](../../../../docs/data_writer_contract_plan.md)
with one documented divergence: `create()` refuses to overwrite an existing
target (h5py mode `"x"`).

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/
  __init__.py                                        # lop_sf_fcc_data_writer_factory
                                                     # (single registration site) + exports
  lop_sf_fcc_trajectory_writer_state.py              # LopSfFccRunMetadata,
                                                     # LopSfFccTrajectoryLayout,
                                                     # LopSfFccTrajectoryWriterState
  lop_sf_fcc_trajectory_writer_behavior.py           # LopSfFccTrajectoryWriterBehavior
  lop_sf_fcc_trajectory_writer_value_object_interface.py  # value-semantics contract
  lop_sf_fcc_trajectory_writer_value_object.py       # HDF5LopSfFccTrajectoryWriterValueObject
  lop_sf_fcc_trajectory_writer_builder_keys.py       # the four builder key constants
  lop_sf_fcc_trajectory_writer_builders.py           # the four concrete builders
  hdf5_lop_sf_fcc_trajectory_data_writer.py          # HDF5LopSfFccTrajectoryDataWriter
```

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/lib/lop_sf_fcc/hdf5_writer/
  conftest.py
  test_data_writer_factory.py
  test_hdf5_lop_sf_fcc_trajectory_data_writer.py
  test_hdf5_lop_sf_fcc_trajectory_write_validation.py
  test_hdf5_lop_sf_fcc_trajectory_writer_append_mode.py
  test_hdf5_lop_sf_fcc_trajectory_writer_value_object.py
  test_lop_sf_fcc_run_metadata.py
  test_lop_sf_fcc_trajectory_layout.py
  test_lop_sf_fcc_trajectory_writer_behavior.py
  test_lop_sf_fcc_trajectory_writer_builders.py
  test_lop_sf_fcc_trajectory_writer_integration.py
  test_lop_sf_fcc_trajectory_writer_scale.py
  test_lop_sf_fcc_trajectory_writer_state.py
  test_lop_sf_fcc_trajectory_writer_value_object_interface.py
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, the as-built writer contract, test
  plan, non-goals, acceptance criteria, and the migration log.
- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.

Feature-specific logic must not leak into the global scope: everything that
exists only to write LOP SF FCC trajectories lives in the `hdf5_writer`
subpackage; reusable writer machinery (the protocol, the exception hierarchy,
the generic single-stream `HDF5DataWriter`) stays in `data_writer_utils`.

## External Dependencies

- **Data writer utils** (`data_writer_utils/`): the generic
  `DataWriterProtocol`, the contract-level exception hierarchy
  (`DataWriterConfigurationError`, `DataWriterLifecycleError`,
  `DataWriterTargetError`), and `HDF5DataWriter` as the structural reference.
  This package has no feature workspace yet; it is governed by the
  project-wide plan.
- **Builder design pattern template**
  (`design_patterns_templates/builder/`): `BuilderRegistry`, `SupportsBuild`,
  `BuilderKeyError`, `BuilderRegistrationError`.
- **Value semantics template**
  (`design_patterns_templates/value_semantics/`): `ValueObjectInterface` and
  the state/behavior protocols the writer value object follows.
- Third-party: h5py and NumPy. All HDF5 (`h5py`) imports live only in
  `hdf5_lop_sf_fcc_trajectory_data_writer.py`.

## Cross-Feature Dependencies

Consumers of this feature:

- **lop_sf_fcc orchestrator** (`lop_sf_fcc_orchestrator_workspaces`):
  `_set_data_writer_attributes` builds the writer value object through
  `lop_sf_fcc_data_writer_factory` under
  `HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey`. See
  [../lop_sf_fcc_orchestrator_workspaces/README.md](../lop_sf_fcc_orchestrator_workspaces/README.md).
- **lop_sf_fcc MDAnalysis backend** (`lop_sf_fcc_mdanalysis_workspaces`):
  `LOP_SF_FCC._conclude` writes frames through the value object
  (`__enter__` creates; `open_for_append()` on later runs). See
  [../lop_sf_fcc_mdanalysis_workspaces/README.md](../lop_sf_fcc_mdanalysis_workspaces/README.md).

Dependencies of this feature — each is documented in both workspaces:

- **Builder design pattern** (`design_patterns_workspaces/builder_design_pattern`):
  `lop_sf_fcc_data_writer_factory` is a `BuilderRegistry` instance with
  exactly one registration site (`hdf5_writer/__init__.py`); the four
  builders satisfy `SupportsBuild`. See
  [../../design_patterns_workspaces/builder_design_pattern/README.md](../../design_patterns_workspaces/builder_design_pattern/README.md).
- **Value semantics** (`design_patterns_workspaces/value_semantics`):
  `HDF5LopSfFccTrajectoryWriterValueObject` follows the
  `StateValueObjectMutable` template behind
  `LopSfFccTrajectoryWriterValueObjectInterface`. See
  [../../design_patterns_workspaces/value_semantics/README.md](../../design_patterns_workspaces/value_semantics/README.md).

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Collection rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
- Backend-neutral writer contract:
  [../../../../docs/data_writer_contract_plan.md](../../../../docs/data_writer_contract_plan.md)
- Orchestrator contract:
  [../lop_sf_fcc_orchestrator_workspaces/top_level_plan.md](../lop_sf_fcc_orchestrator_workspaces/top_level_plan.md)
- MDAnalysis backend contract:
  [../lop_sf_fcc_mdanalysis_workspaces/top_level_plan.md](../lop_sf_fcc_mdanalysis_workspaces/top_level_plan.md)
