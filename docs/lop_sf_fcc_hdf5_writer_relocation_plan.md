# Relocation Plan: LOP SF FCC HDF5 Writer into the lop_sf_fcc Package

Status: **executed 2026-10-05** — full suite green (330 passed, 2 skipped)
before and after. This file is the record of the executed relocation and ICM
conversion; the canonical standing documents now live in the feature
workspace at
[../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/top_level_plan.md).

Branch: feature/plot-order-parameter. Docs+code move; no behavior change.

## Confirmed decisions (2026-10-05)

1. Target: new subpackage
   `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/` holding
   all 7 LOP writer modules, file names unchanged.
2. Registry: a dedicated writer registry (`lop_sf_fcc_data_writer_factory`)
   is owned and populated (4 builders, single site) by the new subpackage's
   `__init__.py`. `data_writer_utils` keeps NO registry. Supersedes the old
   plan's "Registry ownership" section.
3. Workspace folder:
   `workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_hdf5_writer_workspaces/`
   (pre-registered name).
4. `data_writer_utils` retains ONLY generic interface concerns:
   `data_writer_protocol.py`, `exceptions.py`, `hdf5_data_writer.py`,
   `__init__.py` (slimmed exports); `tests/test_hdf5_data_writer.py` stays at
   the tests root. `data_writer_utils` returns to "packages not yet covered
   by a feature workspace" (governed by the project top-level plan).
5. Tests: `tests/data_writer_utils/` (14 files, all LOP-specific) moves to
   `tests/lib/lop_sf_fcc/hdf5_writer/` — mirror of the package path relative
   to the package root (precedent: `tests/design_patterns_templates/builder/`).
6. Docs: `docs/hdf5_lop_sf_fcc_trajectory_writer_value_object_plan.md` →
   absorbed as the feature plan → thin pointer.
   `docs/data_writer_factory_multiple_writers_qa.md` → absorbed as UPDATED
   guidance (per-feature registry replaces the shared-factory pattern) →
   pointer. `docs/concrete_lopsf_fcc_data_writer_plan.md` → absorbed as a
   historical migration-log entry → pointer.
   `docs/data_writer_contract_plan.md` STAYS in docs unchanged (generic
   contract; its 3 inbound links stay).

## Executed steps

### Phase 1 — Code move

1. Created `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/`
   with `__init__.py`.
2. `git mv` of the 7 modules from `data_writer_utils`:
   `lop_sf_fcc_trajectory_writer_{state,behavior,value_object,value_object_interface,builder_keys,builders}.py`,
   `hdf5_lop_sf_fcc_trajectory_data_writer.py`.
3. Rewrote imports inside the moved modules to the new package path. Imports
   of `data_writer_utils.exceptions` STAY (generic boundary).
4. New subpackage `__init__.py` received the 4 `register_builder` calls with
   the registry named `lop_sf_fcc_data_writer_factory`; composite builder
   keeps registry constructor injection; exports moved to `__all__`.
5. Slimmed `data_writer_utils/__init__.py` to the generic interface exports
   (`DataWriterProtocol`, the exception hierarchy, `HDF5DataWriter`).
6. `lib/lop_sf_fcc/__init__.py` re-exports `lop_sf_fcc_data_writer_factory`.
7. `lop_sf_fcc.py` builds through `lop_sf_fcc_data_writer_factory` under
   `HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey`.

### Phase 2 — Test move

8. `git mv tests/data_writer_utils/` → `tests/lib/lop_sf_fcc/hdf5_writer/`.
9. Rewrote test imports; `test_data_writer_factory.py` targets the new
   subpackage (keys, reimport-identity, reload, `__all__`, module strings);
   integration/scale tests and `tests/test_lop_sf_fcc_mdanalysis.py` use the
   renamed registry. `tests/test_hdf5_data_writer.py` unchanged.
10. Full suite: 330 passed, 2 skipped (unchanged).

### Phase 3 — ICM feature workspace

11. Created the feature workspace README.md / top_level_plan.md / context.md
    following the sibling formats; plan absorbs the value-object plan content
    (updated to new paths), the updated "adding another writer" guidance, and
    the relocation migration-log entry.
12. Converted the 3 absorbed docs files to thin pointers.

### Phase 4 — Indexes and cross-references

13. `workspaces/README.md`: tree + Layout Index row → Active with new paths;
    `data_writer_utils/` added to the not-yet-covered list.
14. Grouping `context.md`: writer moved Planned → Active; VisIt plotter
    stays planned.
15. `workspaces/context.md` layout comment updated.
16. Orchestrator + MDAnalysis backend READMEs/plans/context updated to the
    new package paths and registry name; writer feature added to their
    cross-feature links and Related Documents.
17. Grouping `top_level_plan.md` backend-isolation wording updated
    (`h5py` stays in the writer package and generic `data_writer_utils`).
18. `docs/project_plan.md` and `workspaces/top_level_plan.md` Related Plans:
    added the LOP SF FCC HDF5 Writer Plan link.
19. `value_semantics` consumer notes updated to the new interface path.
20. `.github/skills/project-plan/SKILL.md`: unchanged (its
    data_writer_contract_plan.md link stays valid).

## Non-goals / exclusions

- No module or symbol renames beyond the registry name (`lop_sf_fcc_*`
  module prefixes kept to minimize diff).
- No behavior changes to the writer, orchestrator, or backend.
- `data_writer_contract_plan.md` stays in docs/; `data_writer_utils` gets no
  feature workspace in this task.
- No egg-info/pyproject changes (setuptools finds subpackages automatically;
  editable install is path-based).
