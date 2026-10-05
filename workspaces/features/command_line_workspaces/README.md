# Command Line Feature Workspace

## Feature Goal

Own the command-line interface contract for the analysis tools: the
top-level argument parser, one subparser per analysis subcommand, the
validated CLI value classes that store parsed arguments, and the
propagation of validated values to the analysis layer.

The contract guarantees that every value reaching an analysis tool has been
validated twice — once by `argparse` at the command line and once by the CLI
class constructor — so that programmatic construction is just as safe as
command-line parsing.

Currently the only subcommand is `lop_sf_fcc`, whose CLI contract covers:

- `--parallel-threads`: number of parallel execution workers (positive
  integer, default `1`).
- `--md-params-json`: mandatory path to the JSON file holding the molecular
  dynamics simulation parameters.

## Structural Boundaries

Owned production code (this feature's only production scope):

```text
src/lammps_trajectory_analysis_tools/lib/
  lammps_analysis_tool_parser.py        # top-level parser;
                                        # process_command_line_arguments() -> CLI_ID
  lop_sf_fcc/lop_sf_fcc_cli_parser.py   # lop_sf_fcc subparser builder,
                                        # positive_integer/non_blank_string validators,
                                        # CLILopSfFcc, process_lop_sf_fcc_cli_args
src/bin/lammps_analysis_tool.py         # command-line entry point
```

Centralized tests (per the project-wide centralized testing rule, tests never
live inside the feature workspace or `src`):

```text
tests/test_lop_sf_fcc_cli_parser.py
```

Standing plan and status (this folder):

- `top_level_plan.md` — design rules, the as-built CLI contract, test plan,
  non-goals, acceptance criteria, and the completed migration log.
- `context.md` — current implementation status snapshot; must be updated
  whenever the feature's behavior, data flow, or boundaries change.

Feature-specific logic must not leak into the global scope: option parsing,
CLI-class validation, and subcommand wiring belong to the owned modules
above, not to analysis or writer code.

## External Dependencies

- Python standard library only in the parser modules (`argparse`, `typing`).
  The parser itself performs no file I/O and no schema validation.
- JSON schema validation and loading of the `--md-params-json` payload is
  delegated to the shared schemas package at the calculation boundary (see
  below), keeping backend/schema concerns out of the CLI layer.

## Cross-Feature Dependencies

This feature is consumed by, and depends on, the following. Each dependency
is documented in both workspaces.

Consumers:

- **lop_sf_fcc orchestrator feature** (`lop_sf_fcc_orchestrator_workspaces`;
  `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/lop_sf_fcc.py`):
  `LopSfFcc.__call__` receives a `CLILopSfFcc` instance and reads
  `parallel_threads`, `md_params_json`, and the remaining options at the
  calculation boundary in `_set_attributes`. See
  [../lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/README.md](../lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/README.md).

Dependencies of this feature:

- **Builder design pattern template**
  (`design_patterns_templates/builder/`): `LopSfFccSubparserBuilder` is a
  concrete builder registered in the `subparser_builder_registry`
  (`BuilderRegistry`) owned by `lib/lop_sf_fcc/__init__.py`. See
  [../design_patterns_workspaces/builder_design_pattern/README.md](../design_patterns_workspaces/builder_design_pattern/README.md).
- **Schemas package** (`src/lammps_trajectory_analysis_tools/schemas/`):
  `validate_json_file` / `read_json_file` and `md_params.schema.json` are
  used by the lop_sf_fcc calculation boundary to validate and load the MD
  parameters file named by `--md-params-json`.

## Related Documents

- Standing plan: [top_level_plan.md](top_level_plan.md)
- Status snapshot: [context.md](context.md)
- Project-wide rules: [../../top_level_plan.md](../../top_level_plan.md)
- **Parallelization contract** (atom-assignment part owned by the lop_sf_fcc
  orchestrator feature):
  [../lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/top_level_plan.md](../lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/top_level_plan.md)
