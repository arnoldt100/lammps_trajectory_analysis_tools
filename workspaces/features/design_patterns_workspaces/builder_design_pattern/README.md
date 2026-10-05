# Builder Design Pattern Feature Workspace

## Feature Goal

Provide a domain-neutral, key-based builder/registry template for the
`lammps_trajectory_analysis_tools` package, so that every domain family that
produces products through interchangeable concrete builders shares one small,
tested contract instead of re-implementing local registries.

The template generalizes the registry-based builder pattern first used by
`lop_sf_fcc_builder.py`:

- A *product* is the object actually being constructed (e.g. `LoopTimer`).
- A *concrete builder* is a single-step callable:
  `builder(*args, **kwargs) -> Product`.
- A *builder key* is a string uniquely identifying a concrete builder.
- A *registry* maps keys to concrete builders and exposes `register_builder`
  and `build`.

Public API: `SupportsBuild`, `BuilderRegistry`, `BuilderKeyError`,
`BuilderRegistrationError`.

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/design_patterns_templates/builder/
  __init__.py              # public exports
  builder_protocol.py      # SupportsBuild protocol
  builder_registry.py      # BuilderRegistry[P]
  exceptions.py            # BuilderKeyError, BuilderRegistrationError
```

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/design_patterns_templates/builder/
  test_builder_protocol.py
  test_builder_registry.py
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, builder contract, test plan,
  non-goals, acceptance criteria, and the completed migration log.
- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.

Feature-specific logic must not leak into the global scope: anything that is
not a stable, intentionally reusable part of the builder template does not
belong in the owned package.

## External Dependencies

- Python standard library only (`typing`). No third-party packages.
- Domain neutrality is a hard rule: the owned package must not import
  trajectory, analysis, writer, HDF5, MDAnalysis, or any other domain module.

## Cross-Feature Dependencies

This template is consumed by domain features that own their own registry
instance. Each consumer's workspace must document this dependency, and this
section must list every consumer.

Current consumers:

- **Timer utils** (`src/lammps_trajectory_analysis_tools/timer_utils/`):
  owns the single `timer_object_factory` registry, registers
  `LoopTimerBuilder()` under `LoopTimerBuilderKey`, and exposes
  `GeneralTimerBuilder` as a compatibility alias for `BuilderRegistry`.

Planned consumers (not yet migrated; see `context.md`):

- Accumulator builders (`src/lammps_trajectory_analysis_tools/accumulator/`).
- Analysis-tool factories (e.g. `LopSfFccFactory` registry integration).

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Parent workspace rules: [../top_level_plan.md](../top_level_plan.md)
- Project-wide rules: [../../../top_level_plan.md](../../../top_level_plan.md)
