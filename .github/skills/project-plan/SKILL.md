---
name: project-plan
description: 'Top-level engineering standards for the lammps_trajectory_analysis_tools repository. Use when writing, modifying, or reviewing any code in this repo: enforces Python 3.14 syntax, single-underscore private attributes, explicit type signatures with Google-style docstrings, package-qualified imports, pytest conventions, backend isolation, and the pre-merge validation checklist. Distilled from docs/project_plan.md, the canonical project-wide plan that all package and module plans must not weaken.'
---

# Project Plan (Top-Level Engineering Standards)

This skill packages the repository-wide requirements from [docs/project_plan.md](../../../docs/project_plan.md). Package- and module-level plans may add more specific rules, but they must never weaken these project-wide requirements.

## When to Use

- Writing or modifying any production code under `src/lammps_trajectory_analysis_tools`
- Writing or modifying any test code under `tests`
- Reviewing a change before merge
- Changing a public contract, package boundary, import path, or project-wide rule

## Global Design Rules

- Target Python 3.14 and use modern Python 3.14-compatible syntax.
- Keep every class-level and instance-level data attribute private with exactly one leading underscore (e.g. `_state`, `_file`).
- Expose external access through properties or explicit methods; never expose mutable internal storage directly.
- Give every public function, method, and class an explicit type signature and a concise Google-style docstring.
- Keep modules focused on one responsibility; classes stay roughly one page of readable code — split responsibilities beyond that.
- Keep the public API explicit: internal helpers and implementation details must be clearly marked internal and excluded from the supported external contract.
- Prefer small protocols, composition, and focused helpers over inheritance hierarchies or universal abstractions.
- Base classes define the interface only; state and configuration live in concrete subclasses, composition objects, or value objects. A base class may store state only for an extraordinary, documented, approved reason — rare and intentional, never a default pattern.
- Common classes implementing a shared protocol must provide a corresponding builder following the reusable `design_patterns_templates` builder pattern.
- Keep backend-specific dependencies behind the owning integration or adapter boundary.
- Avoid hidden global state, singleton registries, and unrelated resource ownership in reusable value-oriented code.
- Preserve existing public behavior unless a plan explicitly documents a deliberate API change.

## Import and Packaging Rules

- All first-party code lives under the `lammps_trajectory_analysis_tools` package namespace.
- Use package-qualified absolute imports for first-party imports.
- No new `PYTHONPATH`-dependent imports or legacy `src`/module imports.
- Keep dependency direction one-way; resolve circular imports rather than hiding them.
- Keep optional or backend-specific imports in the modules that own those integrations.
- Update package exports when adding a stable public API.
- Keep `pyproject.toml`, package discovery, and the documented Python version aligned.

## Testing Rules

- `src` is production code only — test-only code, fixtures, and data belong under `tests`.
- Use pytest; test functions use the `test_` prefix; use plain `assert` statements, not `unittest.TestCase` methods.
- Test observable behavior and public contracts, not implementation details.
- Add focused tests for new or changed behavior, including invalid input and lifecycle boundaries.
- Preserve ordering, atomicity, and error semantics when a change affects stored or streamed data.
- Run focused tests first, then the complete suite. `src/bin/run_unit_tests.sh` runs all unit tests (`uv run pytest -rA tests` from the repo root, with `PYTHON_GIL=0` and `src` on `PYTHONPATH`).
- Keep integration tests separate from unit tests; use realistic fixtures for external backends.

## Documentation Rules

- Update the owning plan when changing a public contract, package boundary, or project-wide rule.
- Keep public APIs, lifecycle semantics, error policies, and backend limitations documented.
- One canonical rule per repository-wide behavior lives in the top-level plan; link to specialized plans for implementation detail.
- Update architecture or migration docs when module ownership or import paths change.
- Keep examples consistent with the current package namespace and public API.

## Pre-Merge Validation Checklist

Run through this checklist before considering any change complete:

1. Focused tests for the changed behavior pass.
2. The complete pytest suite passes (`src/bin/run_unit_tests.sh`).
3. Static diagnostics and type checking introduce no new errors in changed files.
4. A repository scan confirms no new public class or instance data attributes.
5. First-party imports use the canonical package namespace.
6. Public API and plan documentation match the implementation.
7. Backend boundaries remain intact; no unrelated dependencies leak into core modules.

## Definition of Done

A change is complete when its implementation, tests, documentation, and package boundaries agree; focused and full test suites pass; no new diagnostics are introduced; and every rule above remains satisfied.

## Related Plans

- [Data Writer Contract Plan](../../../docs/data_writer_contract_plan.md)
- [Design Patterns Templates Plan](../../../docs/design_patterns_templates_plan.md)
- [Builder Design Pattern Plan](../../../docs/builder_design_pattern_plan.md)
- [MDAnalysis Integration Plan](../../../docs/mdanalysis_integration_plan.md)
- [Module Migration Path Plan](../../../docs/module_migration_path_plan.md)
- [Architecture](../../../ARCHITECTURE.md)
