# Context - Design Patterns Workspaces

Grouping workspace for all reusable design-pattern template features under
`src/lammps_trajectory_analysis_tools/design_patterns_templates/`.

## Purpose

Each child folder is the ICM feature workspace for one design-pattern
template: it holds the feature's README (goal and boundaries), context
(status snapshot), and top-level plan (standing rules and contract).
Production code stays in `src/`; tests stay centralized in
`tests/design_patterns_templates/`, mirroring the feature structure.

## Feature Index

- [builder_design_pattern/](builder_design_pattern/README.md) — domain-neutral
  key-based builder registry (`SupportsBuild`, `BuilderRegistry`,
  `BuilderKeyError`, `BuilderRegistrationError`). Active; template and tests
  implemented, timer migration complete.
- [value_semantics/](value_semantics/README.md) — value-oriented object
  templates (immutable/mutable state-value wrappers, behavior protocol,
  interface, validation helpers, example owned-state types). Active; package
  and tests implemented, Phase 5 expansion evaluation complete.

## Rules

- Every child feature must keep its template domain-neutral (no trajectory,
  analysis, writer, HDF5, or MDAnalysis imports).
- Every child feature must document cross-feature consumers in its README,
  and consumers must document the dependency back.
- Shared rules for all children live in [top_level_plan.md](top_level_plan.md)
  and inherit from [../../top_level_plan.md](../../top_level_plan.md).
