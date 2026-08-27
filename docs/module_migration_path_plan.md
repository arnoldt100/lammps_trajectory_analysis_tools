# Module Migration Path Plan

## Objective
Migrate from ad hoc import paths and PYTHONPATH-dependent module loading to a standard src-based package namespace with stable absolute imports.

## Historical Note
This document intentionally includes legacy paths and import examples as before/after mapping guidance.
When running repository-wide grep checks for active legacy usage, exclude this file.

## Target Namespace
Use one package root for all importable code:

- `lammps_trajectory_analysis_tools`

## Current to Target Module Mapping

### Top-level source modules
- `src/__init__.py` -> `src/lammps_trajectory_analysis_tools/__init__.py`
- `src/analysis.py` -> `src/lammps_trajectory_analysis_tools/analysis.py`
- `src/trajectory.py` -> `src/lammps_trajectory_analysis_tools/trajectory.py`
- `src/plotting.py` -> `src/lammps_trajectory_analysis_tools/plotting.py`
- `src/utils.py` -> `src/lammps_trajectory_analysis_tools/utils.py`

### Library package
- `src/lib/__init__.py` -> `src/lammps_trajectory_analysis_tools/lib/__init__.py`
- `src/lib/data_types.py` -> `src/lammps_trajectory_analysis_tools/lib/data_types.py`
- `src/lib/lammps_analysis_tool_parser.py` -> `src/lammps_trajectory_analysis_tools/lib/lammps_analysis_tool_parser.py`

### Accumulator subpackage
- `src/lib/accumulator/__init__.py` -> `src/lammps_trajectory_analysis_tools/accumulator/__init__.py`
- `src/lib/accumulator/array_accumulator.py` -> `src/lammps_trajectory_analysis_tools/accumulator/array_accumulator.py`
- `src/lib/accumulator/merge_accumulators.py` -> `src/lammps_trajectory_analysis_tools/accumulator/merge_accumulators.py`

### LOP/SF FCC subpackage
- `src/lib/lop_sf_fcc/__init__.py` -> `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/__init__.py`
- `src/lib/lop_sf_fcc/lop_sf_fcc.py` -> `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc.py`
- `src/lib/lop_sf_fcc/lop_sf_fcc_builder.py` -> `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc_builder.py`
- `src/lib/lop_sf_fcc/lop_sf_fcc_cli_parser.py` -> `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc_cli_parser.py`

### New integration area (MDAnalysis)
- `src/integrations/mdanalysis/*` (original plan) -> `src/lammps_trajectory_analysis_tools/integrations/mdanalysis/*`

## Import Rewrite Rules

### Rule 0: Keep class data private
- Prefix every class-level and instance-level data attribute with a single leading underscore.
- Expose required external access through properties rather than public mutable storage.

### Rule 1: Replace implicit local imports with package-qualified imports
- Before: `from data_types import AtomCoordinates`
- After: `from lammps_trajectory_analysis_tools.lib.data_types import AtomCoordinates`

### Rule 2: Replace sibling imports with absolute imports
- Before: `from accumulator.array_accumulator import ArrayAccumulator`
- After: `from lammps_trajectory_analysis_tools.accumulator.array_accumulator import ArrayAccumulator`

### Rule 3: Keep one canonical import style across src, tests, and scripts
- Use only `from lammps_trajectory_analysis_tools...` imports for project code.

## Packaging Changes

### pyproject.toml updates
1. Add setuptools package-dir mapping:
- `package-dir = {"" = "src"}`

2. Enable package discovery from `src`:
- `tool.setuptools.packages.find.where = ["src"]`
- Optionally set include pattern for `lammps_trajectory_analysis_tools*`

3. Install locally in editable mode for development:
- `pip install -e .`

## Execution Environment Changes

### Environment scripts
- Remove hard dependency on PYTHONPATH for project imports.
- Keep PATH updates for CLI scripts if needed.
- If transition period is required, temporarily support both:
  - package import path via editable install
  - legacy PYTHONPATH entries

## Migration Phases

### Phase 1: Namespace scaffold
- Create `src/lammps_trajectory_analysis_tools/` with `__init__.py`.
- Copy/move modules preserving relative structure.

### Phase 2: Update imports in src
- Rewrite imports in all modules under `src/lammps_trajectory_analysis_tools/`.
- Resolve circular imports if discovered.

### Phase 3: Update imports in tests
- Rewrite imports in `tests/` to package-qualified paths.
- Validate test fixtures that currently depend on PYTHONPATH.

### Phase 4: Wire packaging
- Update `pyproject.toml` package discovery.
- Run editable install.

### Phase 5: Validation and cleanup
- Run unit tests and integration tests.
- Remove obsolete path assumptions from env scripts.
- Document new import policy in README.

## Validation Checklist
- `python -c "import lammps_trajectory_analysis_tools"` succeeds.
- `python -c "from lammps_trajectory_analysis_tools.lib.data_types import Box"` succeeds.
- Test suite runs without PYTHONPATH customization.
- CLI entry scripts still function with updated imports.
- Legacy-import scan is clean for active code paths. Example:
  `rg -n "src/lib|PYTHONPATH=.*src/lib|from data_types import|from lop_sf_fcc|from accumulator" -S src tests README.md ARCHITECTURE.md docs --glob '!docs/module_migration_path_plan.md'`

## Rollback Strategy
- Keep migration in small commits by phase.
- If breakage occurs, revert only the latest phase commit.
- Preserve a short transition window where PYTHONPATH still includes legacy paths until tests are fully green.

## Definition of Done
- All first-party modules live under `src/lammps_trajectory_analysis_tools/`.
- All first-party imports are absolute and package-qualified.
- Test and runtime workflows no longer rely on PYTHONPATH for project code discovery.
- MDAnalysis adapters live under `lammps_trajectory_analysis_tools.integrations.mdanalysis`.
