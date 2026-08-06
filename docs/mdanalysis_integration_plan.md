# MDAnalysis Integration Plan

## Objective
Establish a clear organizational structure for MDAnalysis-specific code so the core analysis package remains backend-agnostic and easier to test.

## Proposed Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    integrations/
      __init__.py
      mdanalysis/
        __init__.py
        universe.py
        selection.py
        transform.py
        conversion.py
        analysis_bridge.py
        config.py
        errors.py
```

## Design Rules
- Keep all MDAnalysis imports inside `src/lammps_trajectory_analysis_tools/integrations/mdanalysis/*`.
- Keep core analysis modules free of direct MDAnalysis imports.
- Expose a minimal stable API from `src/lammps_trajectory_analysis_tools/integrations/mdanalysis/__init__.py`.
- Use explicit conversion names:
  - `to_internal_*` for conversion into project-native structures.
  - `from_mda_*` for conversion from MDAnalysis objects.
- Prefer thin adapters in `analysis_bridge.py`; keep scientific logic in core modules.

## Public API (Initial)
- `load_universe(topology_path, trajectory_path, **kwargs)`
- `select_atoms(universe_mda, selection_query)`
- `to_internal_trajectory(universe_mda)`
- `run_lop_sf_fcc_from_universe(universe_mda, **kwargs)`

## Migration Phases

### Phase 1: Scaffolding
- Create `src/lammps_trajectory_analysis_tools/integrations/mdanalysis/` package and empty module files.
- Add module docstrings clarifying each file responsibility.
- Export initial API functions in `__init__.py`.

### Phase 2: Move IO + Conversion
- Move Universe creation/loading logic into `universe.py`.
- Move object/data mapping logic into `conversion.py`.
- Replace direct call sites with adapter calls.

### Phase 3: Bridge Existing Analysis
- Add bridge entry points in `analysis_bridge.py` that:
  - validate MDAnalysis inputs,
  - convert to internal structures,
  - call core analysis functions,
  - return typed outputs.

### Phase 4: Selection + Transform Utilities
- Centralize repeated selection patterns in `selection.py`.
- Add frame/coordinate preprocessing in `transform.py`.

### Phase 5: Test Coverage
- Add unit tests for each adapter module.
- Add contract tests to verify adapter outputs match core analysis input expectations.
- Add end-to-end tests using existing example trajectory files.

## Test Layout Proposal

```text
tests/
  integrations/
    mdanalysis/
      test_universe.py
      test_selection.py
      test_transform.py
      test_conversion.py
      test_analysis_bridge.py
```

## Milestone 1 (Minimal Delivery)
- Implement:
  - `universe.py`
  - `conversion.py`
  - one bridge function in `analysis_bridge.py`
- Add 2-3 contract tests covering the Ar4 workflow.
- Confirm no direct MDAnalysis imports remain in core analysis modules.

## Risks and Mitigations
- Risk: leakage of MDAnalysis types into core logic.
  - Mitigation: strict adapter boundary and conversion contracts.
- Risk: behavior drift during migration.
  - Mitigation: contract tests before/after migration.
- Risk: oversized bridge layer.
  - Mitigation: keep bridge functions thin and push reusable logic into core modules.

## Acceptance Criteria
- MDAnalysis-specific code is isolated under `src/lammps_trajectory_analysis_tools/integrations/mdanalysis/`.
- Core modules run without importing MDAnalysis.
- Integration tests validate end-to-end path from Universe input to analysis output.
- Public integration API is documented and stable.
