# Parallelize Over Trajectories Plan

This plan has moved to the lop_sf_fcc_mdanalysis ICM feature workspace:

- Standing plan (design rules, backend contract, test plan, non-goals,
  acceptance criteria, and the Stage 1/Stage 2 migration log including the
  benchmark results):
  [lop_sf_fcc_mdanalysis_workspaces/top_level_plan.md](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_mdanalysis_workspaces/top_level_plan.md)
- Feature goal, structural boundaries, and cross-feature dependencies:
  [README.md](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_mdanalysis_workspaces/README.md)
- Implementation status snapshot:
  [context.md](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_mdanalysis_workspaces/context.md)

The orchestrator-side wiring (`_backend_run_arguments`,
`--parallel-threads` consumption) is owned by the orchestrator feature:
[lop_sf_fcc_orchestrator_workspaces/top_level_plan.md](../workspaces/features/lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/top_level_plan.md).

This file remains only as a stable link target for existing references; it
carries no content of its own. Update the workspace files, not this file.
