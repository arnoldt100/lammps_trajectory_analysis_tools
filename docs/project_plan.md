# Project Engineering Plan

## Purpose

This document contains requirements that apply to the entire repository. Package and module plans may add more specific rules, but they must not weaken these project-wide requirements.

## Global Design Rules

- Target Python 3.14 and use modern Python 3.14-compatible syntax.
- Keep every class-level and instance-level data attribute private with exactly one leading underscore, such as `_state` or `_file`.
- Expose required external access through properties or explicit methods; do not expose mutable internal storage directly.
- Give every public function, method, and class an explicit type signature and a concise Google-style docstring.
- Keep modules focused on one responsibility and avoid classes and functions that grow beyond what can be understood and tested locally.
- Prefer small protocols, composition, and focused helpers over unnecessary inheritance hierarchies or universal abstractions.
- Common classes that implement a shared protocol must provide a corresponding builder that follows the reusable `design_patterns_templates` builder pattern.
- Keep backend-specific dependencies behind the owning integration or adapter boundary.
- Avoid hidden global state, singleton registries, and unrelated resource ownership in reusable value-oriented code.
- Preserve existing public behavior unless a plan explicitly documents a deliberate API change.

## Import And Packaging Rules

- Keep all first-party code under the `lammps_trajectory_analysis_tools` package namespace.
- Use package-qualified absolute imports for first-party imports.
- Do not introduce new `PYTHONPATH`-dependent imports or legacy `src`/module imports.
- Keep dependency direction one-way and resolve circular imports rather than hiding them.
- Keep optional or backend-specific imports in the modules that own those integrations.
- Update package exports when adding a stable public API.
- Keep `pyproject.toml`, package discovery, and the documented Python version aligned.

## Testing Rules

- Use pytest for tests and fixtures; test functions must use the `test_` prefix.
- Use plain `assert` statements and pytest assertions rather than `unittest.TestCase` methods.
- Test observable behavior and public contracts rather than implementation details.
- Add focused tests for new or changed behavior, including invalid input and lifecycle boundaries where applicable.
- Preserve ordering, atomicity, and error semantics when a change affects stored or streamed data.
- Run the focused tests first, then the complete suite before considering a change complete.
- Keep integration tests separate from unit tests and use realistic fixtures for external backends.

## Documentation Rules

- Update the owning plan when changing a public contract, package boundary, or project-wide rule.
- Keep public APIs, lifecycle semantics, error policies, and backend limitations documented.
- Prefer one canonical rule in this document for repository-wide behavior; link to specialized plans for implementation detail.
- Update architecture or migration documentation when module ownership or import paths change.
- Keep examples consistent with the currently supported package namespace and public API.

## Validation Checklist

Before merging a change:

- The focused tests for the changed behavior pass.
- The complete pytest suite passes.
- Static diagnostics and type checking introduce no new errors in changed files.
- A repository scan confirms no new public class or instance data attributes.
- First-party imports use the canonical package namespace.
- Public API and plan documentation match the implementation.
- Backend boundaries remain intact and no unrelated dependencies leak into core modules.

## Project Workstreams

1. **Package and import migration**: maintain the standard `src` layout, package-qualified imports, and editable-install workflow.
2. **Core trajectory and analysis**: keep data structures, calculations, and plotting responsibilities separated and testable.
3. **Backend integrations**: isolate MDAnalysis and storage backends behind explicit adapter contracts.
4. **Reusable design templates**: keep value semantics and validation helpers domain-neutral and private-state compliant.
5. **Contract testing**: reuse backend-independent tests wherever multiple implementations provide the same behavior.

## Definition Of Done

A project change is complete when its implementation, tests, documentation, and package boundaries agree; focused and full test suites pass; no new diagnostics are introduced; and the global rules in this plan remain satisfied.

## Related Plans

- [Data Writer Contract Plan](data_writer_contract_plan.md)
- [Design Patterns Templates Plan](design_patterns_templates_plan.md)
- [Builder Design Pattern Plan](builder_design_pattern_plan.md)
- [MDAnalysis Integration Plan](mdanalysis_integration_plan.md)
- [Module Migration Path Plan](module_migration_path_plan.md)
- [Architecture](../ARCHITECTURE.md)
