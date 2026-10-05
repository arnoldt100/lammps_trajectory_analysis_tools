# Context - Workspaces Root

This directory is the root of the Interpretable Context Methodology (ICM)
organization for the repository, as defined in
`.github/copilot-instructions.md`.

## Purpose

- Keep operational context for a feature scoped to its own workspace folder.
- Keep feature plans, boundaries, and status snapshots out of global modules
  and close to the feature they describe.
- Leave `src/` for production code and `tests/` for centralized tests only.

## Layout

```text
workspaces/
  context.md           # this file — ICM root purpose and index
  top_level_plan.md    # project-wide engineering rules (all features inherit)
  features/            # one workspace folder per feature or feature group
    design_patterns_workspaces/
      ...              # builder_design_pattern/ (active), value_semantics (active)
    command_line_workspaces/
      ...              # command_line feature (active)
    lop_sf_fcc_workspaces/
      ...              # lop_sf_fcc collection: lop_sf_fcc_orchestrator_workspaces/,
                       # lop_sf_fcc_mdanalysis_workspaces/, and
                       # lop_sf_fcc_hdf5_writer_workspaces/ (active);
                       # lop_sf_fcc_visit_plotter_workspaces/ (planned)
```

## Feature Folder Convention

Each feature folder contains:

- `README.md` — feature goal, structural boundaries, external dependencies,
  and cross-feature dependencies.
- `context.md` — current implementation status snapshot; updated whenever the
  feature's behavior, data flow, or boundaries change.
- `top_level_plan.md` — the feature's standing plan: design rules, contracts,
  test plan, non-goals, and acceptance criteria. Must not weaken
  [top_level_plan.md](top_level_plan.md).

## Working Rules

- Before modifying code for a feature, review its workspace folder first.
- Do not pull unrelated files into scope; shared dependencies must be
  documented in both folders' README files.
- If a change alters a feature's behavior, data flow, or state management,
  update that feature's workspace documentation in the same change.
