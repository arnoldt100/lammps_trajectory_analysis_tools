# Context - Builder Design Pattern

Status snapshot for the builder design pattern feature. Per the ICM rules,
this file must be updated whenever the feature's behavior, data flow, or
boundaries change.

Last reviewed: 2026-10-04.

## Implementation Status

### Done

- Template package implemented and exported:
  `src/lammps_trajectory_analysis_tools/design_patterns_templates/builder/`
  with `SupportsBuild`, `BuilderRegistry`, `BuilderKeyError`, and
  `BuilderRegistrationError`.
- Contract tests in place and passing:
  `tests/design_patterns_templates/builder/test_builder_registry.py` and
  `tests/design_patterns_templates/builder/test_builder_protocol.py`,
  covering the full test plan in `top_level_plan.md` (registration, argument
  forwarding, duplicate registration, unknown keys, registry independence).
- Timer migration complete:
  - `timer_utils/__init__.py` owns the single `timer_object_factory` and is
    the only registration site.
  - `LoopTimerBuilder` is a direct callable builder; `LoopTimerBuilderKey`
    is unchanged.
  - `GeneralTimerBuilder` is now a compatibility alias for
    `BuilderRegistry`; its module no longer creates a factory.
- Feature workspace converted to ICM on 2026-10-04; the former canonical
  document `docs/builder_design_pattern_plan.md` is now a pointer here.

### Pending

- Accumulator builder migration: adopt `BuilderRegistry` for the accumulator
  family (see the accumulator refactor plans under `docs/`).
- Analysis-tool factory registry integration (e.g. `LopSfFccFactory`), per
  the migration sketch in `top_level_plan.md`.

### Not planned

- Product-specific validation or construction logic inside the template.
- Builder base classes or zero-arg-construct-then-call flows.
- Silent registration overwrite.

## Current Data Flow

```text
domain package (e.g. timer_utils/__init__.py)
  instantiates its own BuilderRegistry[P]
  registers concrete builder instances under string keys
        │
caller calls registry.build(key, *args, **kwargs)
        │
registry looks up key ──missing──▶ raises BuilderKeyError
        │
forwards *args, **kwargs to the registered callable
        │
returns the product to the caller
```

There is no shared or hidden registry state: each domain owns its own
`BuilderRegistry` instance.

## Maintenance Rule

Any change to the public contract (`SupportsBuild`, `BuilderRegistry`, the
exceptions, or the package layout) requires, in the same change:

1. Updated contract tests under `tests/design_patterns_templates/builder/`.
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every consumer listed in `README.md` (currently
   `timer_utils`).
