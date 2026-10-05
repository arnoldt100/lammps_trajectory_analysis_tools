# Top Level Plan - LOP SF FCC Workspaces

This plan governs every feature under
`workspaces/features/lop_sf_fcc_workspaces/`. It inherits all project-wide
rules from [../../top_level_plan.md](../../top_level_plan.md) and adds rules
shared by all `lop_sf_fcc` features; child feature plans must not weaken
either level.

## Purpose Of The Collection

This collection is the home for every feature of the `lop_sf_fcc` analysis
tool — the calculation of the FCC structure-factor local order parameter.
Each child feature owns one stage or backend of the tool: orchestration, the
MDAnalysis calculation backend, and (planned) output writers and plotters.

## Shared Design Rules

- **One-way dependency direction:** command_line → orchestrator →
  backend/writer/plotter children. Children never import from their
  consumers, and sibling features interact only through documented contracts
  (recorded in both READMEs).
- **Physics lives only in backend features:** the orchestrator and writer or
  plotter features must not contain order-parameter calculation code.
- **Registries are owned per package:** each child that participates in the
  builder pattern documents which registry it owns or consumes; registration
  sites stay in the owning package's `__init__.py`.
- **Private state:** every class-level and instance-level data attribute in
  owned production code is private with exactly one leading underscore;
  external access goes through properties or explicit methods.
- **Backend isolation:** MDAnalysis imports stay in the backend feature and
  the `integrations/mdanalysis` package; `h5py` imports stay in the writer
  feature package (`lib/lop_sf_fcc/hdf5_writer/`) and the generic
  `data_writer_utils` package.
- **Expansion requires a demonstrated consumer:** add a child feature only
  when the owning production code exists or is actively planned (see the
  planned writer and plotter entries in [context.md](context.md)).

## Testing Rules

- Tests are centralized under `tests/`, mirroring the feature structure; no
  tests live inside a feature workspace or `src`.
- Every child feature lists its owned test files in its README.
- End-to-end and backend-matrix tests cross child boundaries deliberately;
  unit tests should stay within one child's contract.

## Documentation Rules

- Each child feature keeps its own `README.md` (goal, boundaries,
  dependencies), `context.md` (status snapshot), and `top_level_plan.md`
  (standing rules and contract), and must link back to this plan.
- Cross-feature consumers and dependencies are recorded in both features'
  READMEs.
- Completed migrations are recorded in the child plan's migration log, not
  left as open work items.

## Feature Index

See [context.md](context.md) for the current list of child features and
their status.
