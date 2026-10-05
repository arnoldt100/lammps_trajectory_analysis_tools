# Value Semantics Feature Workspace

## Feature Goal

Provide a domain-neutral value-semantics template package for
`lammps_trajectory_analysis_tools`: a small pattern library for value-oriented
domain objects whose identity is their state. The package supplies:

- value-object wrappers that own state (`StateValueObjectImmutable`,
  `StateValueObjectMutable`);
- a behavior protocol describing how state is copied, validated, compared,
  replaced, updated, represented, and hashed (`StateValueBehaviorProtocol`);
- an abstract interface for value-oriented objects (`ValueObjectInterface`)
  and a minimal runtime-checkable protocol (`ValueSemantics`);
- validation primitives (`ValueValidationError`, `validate_state`);
- helper functions operating on both wrapper types (`hash_state`,
  `invoke_dummy_method`);
- two concrete owned-state examples (`ConcreteStateImplementation`,
  `NumericStateImplementation`) demonstrating adaptation without inheritance
  from the wrappers and without per-type helper modules.

Core principles:

- objects are defined by their state rather than identity;
- equal state produces equal values;
- copies are independent unless sharing is explicit and documented;
- invariants are established at construction or controlled update boundaries;
- operations are predictable, composable, and easy to test.

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/design_patterns_templates/value_semantics/
  __init__.py                                # public exports
  protocols.py                               # StateValueBehaviorProtocol, ValueSemantics
  value_object_interface.py                  # ValueObjectInterface (ABC, stateless)
  state_value_object_immutable.py            # StateValueObjectImmutable
  state_value_object_mutable.py              # StateValueObjectMutable
  value_object_behaviors.py                  # hash_state, invoke_dummy_method
  validation.py                              # ValueValidationError, validate_state
  concrete_state_implementation.py           # example owned state object
  concrete_state_implementation_helpers.py   # example shared helpers
  numeric_state_implementation.py            # second example owned state object
```

The package is re-exported selectively from
`design_patterns_templates/__init__.py` (`StateValueObjectImmutable`,
`StateValueObjectMutable`).

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/design_patterns_templates/value_semantics/
  test_value_object.py
  test_value_object_behaviors.py
  test_validation.py
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, as-built contract, test plan,
  non-goals, acceptance criteria, and the completed migration log.
- `context.md` — current implementation status snapshot and the decision log;
  must be updated whenever the feature's behavior, data flow, or boundaries
  change.

Feature-specific logic must not leak into the global scope: anything that is
not a stable, intentionally reusable part of the value-semantics template
does not belong in the owned package.

## External Dependencies

- Python standard library only (`abc`, `collections.abc`, `typing`).
- Domain neutrality is a hard rule: the owned package must not import
  trajectory, analysis, writer, HDF5, MDAnalysis, or any other domain module.

## Cross-Feature Dependencies

This template is consumed by domain features. Each consumer supplies its own
`StateValueBehaviorProtocol` implementation (and typically its own owned
state type); the template never imports its consumers. Each consumer's
workspace must document this dependency once it has an ICM workspace, and
this section must list every consumer.

Current consumers:

- **Accumulator** (`src/lammps_trajectory_analysis_tools/accumulator/`):
  `array_accumulator_value.py` builds accumulator values on
  `StateValueObjectImmutable` and satisfies `ValueSemantics`;
  `array_accumulator.py` uses `StateValueObjectMutable` with its own concrete
  state and behavior.
- **LOP SF FCC HDF5 writer**
  (`src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/`):
  `lop_sf_fcc_trajectory_writer_value_object_interface.py` subclasses
  `ValueObjectInterface` for the HDF5 trajectory-writer value object. Owned
  by
  [lop_sf_fcc_hdf5_writer_workspaces](../../lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/README.md).
- Consumer-side tests: `tests/test_array_accumulator_contract.py`,
  `tests/lib/lop_sf_fcc/hdf5_writer/`.

Sibling feature: [builder_design_pattern](../builder_design_pattern/README.md)
— domain families commonly combine both templates (value objects built
through a shared builder registry).

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot and decision log: [context.md](context.md)
- Usage guide (how to copy and adapt the template in a domain project):
  [docs/value_semantics_package_usage_guide.md](../../../../docs/value_semantics_package_usage_guide.md)
- Parent workspace rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
