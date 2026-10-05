# Context - Command Line

Status snapshot for the command-line feature. Per the ICM rules, this file
must be updated whenever the feature's behavior, data flow, or boundaries
change.

Last reviewed: 2026-10-04.

## Implementation Status

### Done

- Top-level parser and subcommand wiring:
  `lib/lammps_analysis_tool_parser.py` builds the top-level parser, builds
  subparsers through `subparser_builder_registry`, and returns the typed
  `CLI_ID` union (currently `CLILopSfFcc`); entry point is
  `src/bin/lammps_analysis_tool.py`.
- `--parallel-threads` contract implemented: `positive_integer` validator,
  default `1`, constructor-level `TypeError`/`ValueError` validation,
  read-only property, propagation to `LopSfFcc`, and backend selection via
  `_backend_run_arguments` (serial for `1`, multiprocessing `n_workers`
  otherwise, with an `os.cpu_count()` warning).
- `--md-params-json` contract implemented: mandatory option,
  `non_blank_string` validator, constructor rejection of `None`, schema
  validation against `schemas/md_params.schema.json` at the calculation
  boundary (`validate_json_file`/`read_json_file`), and propagation to the
  data-writer metadata value object.
- Contract tests in place and passing: `tests/test_lop_sf_fcc_cli_parser.py`
  covers the full test plan in `top_level_plan.md` (defaults, valid/invalid
  CLI values, programmatic construction errors, help epilog).
- Feature workspace converted to ICM on 2026-10-04; the former canonical
  documents under `docs/command_line/` are now pointers here.

### Pending

- Remove the leftover debug `print(f"Error value: {md_params_json}")` in
  `CLILopSfFcc.__init__` (`lop_sf_fcc_cli_parser.py`).
- Constructor blank-string validation quirk: the constructor check
  `md_params_json.strip() == "a"` rejects only the literal string `"a"`
  instead of any blank string. Command-line input is still safe (the
  `non_blank_string` parser rejects blanks), but direct construction with
  `"   "` currently passes. Fix the comparison to reject blank strings and
  add a direct-construction test for blank `md_params_json`.

### Not planned

- Option aliases such as `--threads` or `--nthreads`.
- JSON schema validation or file I/O inside the parser modules (kept at the
  calculation boundary).
- Thread pools/executors in the CLI layer (owned by the parallelization
  plan).

## Decision Log

- Both `docs/command_line/` plans were converted into this single feature
  workspace because they describe one CLI contract (`CLILopSfFcc`); each is
  recorded as a completed migration in `top_level_plan.md`.
- The CLI layer deliberately performs no schema validation: `--md-params-json`
  carries only a validated non-blank path; content validation happens where
  the file is consumed (`LopSfFcc._set_attributes`).
- `--parallel-threads` semantics moved past the original plan's "stay
  serial" step once the parallelization work wired the value into backend
  selection; the CLI contract itself is unchanged.

## Current Data Flow

```text
argv
  │
top-level ArgumentParser (lammps_analysis_tool_parser.py)
  │  subparser built by subparser_builder_registry.build("lop_sf_fcc", ...)
  ▼
argparse parsing (positive_integer / non_blank_string validators)
  │  invalid values ──▶ argparse error (SystemExit)
  ▼
CLILopSfFcc(**vars(args))            # constructor re-validates
  │  invalid values ──▶ TypeError / ValueError
  ▼
LopSfFcc.__call__(command_line_arguments)
  │
  ├─ parallel_threads ──▶ _backend_run_arguments ──▶ run backend
  │                        (serial if 1, multiprocessing otherwise)
  └─ md_params_json ──▶ validate_json_file vs md_params.schema.json
                        ──▶ read_json_file ──▶ data-writer metadata
```

## Maintenance Rule

Any change to the CLI contract (options, validators, `CLILopSfFcc` fields,
subcommand wiring, or the propagation boundary) requires, in the same change:

1. Updated contract tests under `tests/test_lop_sf_fcc_cli_parser.py`.
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every consumer listed in `README.md` (currently the
   lop_sf_fcc orchestrator feature, workspace
   `lop_sf_fcc_workspaces/lop_sf_fcc_orchestrator_workspaces/`) and of
   the schemas package dependency.
