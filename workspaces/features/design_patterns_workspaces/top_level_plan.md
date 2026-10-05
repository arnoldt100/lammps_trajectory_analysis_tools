# Top Level Plan - Design Patterns Workspaces

This plan governs every design-pattern template feature under
`workspaces/features/design_patterns_workspaces/`. It inherits all
project-wide rules from [../../top_level_plan.md](../../top_level_plan.md)
and adds rules shared by all pattern-template features; child feature plans
must not weaken either level.

## Purpose Of The Collection

This collection is a reusable home for design-pattern templates that provide
starting points for new implementations without coupling them to a specific
analysis domain. Templates are starting points, not mandated base classes: a
domain implementation may compose, adapt, or copy a template rather than
inherit from it.

## Shared Design Rules

- **Domain neutrality:** template packages must not import trajectory,
  analysis, writer, HDF5, MDAnalysis, or any other domain module. Standard
  library and `typing` only, unless a child plan explicitly justifies an
  addition.
- **Private state:** every class-level and instance-level data attribute is
  private with exactly one leading underscore; external access goes through
  properties or explicit methods.
- **No hidden global state:** no singleton registries or shared module-level
  mutable state in template packages. Domain modules instantiate and own
  their own instances.
- **Small, composable templates:** prefer small protocols and composition
  over inheritance-heavy frameworks. Keep templates small enough that a
  domain implementation can understand and adapt them rather than inherit
  accidental policy.
- **Explicit public API:** each template package exports only stable,
  intentionally reusable names through its `__init__.py`.
- **Naming describes behavior:** use names that describe behavior rather than
  the eventual domain (e.g. `StateValueObjectImmutable`), and avoid a generic
  base class when a dataclass, protocol, or helper function is clearer.
- **Expansion requires demonstrated reuse:** add a new template or capability
  only when a repeated use case demonstrates that it belongs in the shared
  package, with documented semantics; do not expand on speculation.

## Testing Rules

- Tests are centralized under `tests/design_patterns_templates/`, mirroring
  the template package structure.
- Every template feature ships contract tests covering its public contract,
  error semantics, and instance independence.
- Contract tests must not depend on domain code; use minimal local stand-ins
  (e.g. a dummy `Product`) instead.

## Documentation Rules

- Each feature keeps its own `README.md` (goal, boundaries, dependencies),
  `context.md` (status snapshot), and `top_level_plan.md` (standing rules
  and contract).
- Cross-feature consumers of a template are recorded in the template
  feature's README and in the consumer feature's workspace.
- Completed migrations are recorded in the feature plan's migration log, not
  left as open work items.

## Feature Index

See [context.md](context.md) for the current list of child features and
their status.


