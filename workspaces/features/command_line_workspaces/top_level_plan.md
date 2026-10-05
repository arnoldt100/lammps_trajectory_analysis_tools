# Top Level Plan - Command Line

This is the canonical standing plan for the command-line feature. It inherits
all project-wide rules from
[../../top_level_plan.md](../../top_level_plan.md) and adds feature-specific
rules; it must not weaken the project-wide rules.

## Objective

Maintain the command-line interface contract for the analysis tools: the
top-level parser, one subparser builder per analysis subcommand, the
validated CLI value classes, and the propagation of validated values to the
analysis layer. Every value consumed by an analysis tool is validated at the
command line and again at CLI-class construction.

## Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    lib/
      lammps_analysis_tool_parser.py        # top-level parser, CLI_ID union
      lop_sf_fcc/
        lop_sf_fcc_cli_parser.py            # subparser builder, validators, CLILopSfFcc
  bin/
    lammps_analysis_tool.py                 # entry point

tests/
  test_lop_sf_fcc_cli_parser.py
```

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/command_line_workspaces/
  README.md
  context.md
  top_level_plan.md
```

## Design Rules

- **Dual validation:** every CLI option is validated twice — by an `argparse`
  `type`/`choices` validator at parse time and by the CLI class constructor
  at programmatic construction. The CLI class must reject invalid values
  independently of `argparse`, raising `TypeError` for wrong types and
  `ValueError` for out-of-domain values; it must not silently coerce.
- **Private state:** every CLI-class attribute is stored privately with a
  single leading underscore and exposed through a read-only property.
- **Subparser builder pattern:** each analysis subcommand has a concrete
  builder (e.g. `LopSfFccSubparserBuilder`, a direct callable) registered in
  the `subparser_builder_registry` owned by the subcommand's package
  (`lib/lop_sf_fcc/__init__.py`). Subcommand names are unique; the subcommand
  name doubles as the builder key.
- **Explicit subcommand processing:** the top-level parser maps each
  subcommand name to its `process_*_cli_args` function, which constructs the
  typed CLI object from the parsed namespace.
- **Naming:** command-line spellings are `--kebab-case`; destinations and
  property names are `snake_case`. Do not add option aliases unless a
  project-wide naming convention requires them.
- **Documented defaults:** every optional value states its default and its
  validity requirement in the help text.
- **No backend work in the CLI layer:** the parser modules use only the
  standard library. File I/O, JSON schema validation, and execution-backend
  selection happen at the calculation boundary, not in the parser.

## CLI Contract (as built)

### Subcommands

- `lop_sf_fcc` — calculates the local FCC order parameter structure factor.
  Its epilog documents the `LTAT_DEBUG_PLOT_FRAMES` environment variable.

### `CLILopSfFcc`

Stores the parsed `lop_sf_fcc` arguments; every field is private with a
read-only property:

| Constructor argument  | Type                    | Default          | Option spelling        |
|-----------------------|-------------------------|------------------|------------------------|
| `subcommand_name`     | `Optional[str]`         | `None`           | (subparser dest)       |
| `trajectory`          | `Optional[str]`         | `None`           | `--trajectory` (req.)  |
| `psf`                 | `Optional[str]`         | `None`           | `--psf` (req.)         |
| `edge_length`         | `Optional[float]`       | `None`           | `--edge-length` (req.) |
| `output`              | `Optional[str]`         | `None`           | `--output`             |
| `timeunits`           | `Optional[str]`         | `None`           | `--timeunits` (req., choices `["ps"]`) |
| `dt`                  | `Optional[float]`       | `None`           | `--dt` (req.)          |
| `cutoff`              | `Optional[float]`       | `None`           | `--cutoff` (req.)      |
| `output_hdf5_file`    | `Optional[str]`         | `None`           | `--output-hdf5-file`   |
| `parallel_threads`    | `int`                   | `1`              | `--parallel-threads`   |
| `do_data_analysis`    | `Optional[Callable]`    | `None`           | (set via `set_defaults`) |
| `md_params_json`      | `Optional[str]`         | `None`           | `--md-params-json` (req.) |

### Validators

- `positive_integer(value: str) -> int` — parses a strictly positive integer;
  raises `argparse.ArgumentTypeError` for zero, negative, or non-integer
  input.
- `non_blank_string(value: str) -> str` — strips leading/trailing whitespace;
  raises `argparse.ArgumentTypeError` for non-strings and for strings that
  are empty after stripping.

### `--parallel-threads`

- Default `1`; only positive integers are accepted.
- Parser: `type=positive_integer` (invalid values fail with an `argparse`
  error before the calculation starts).
- Constructor: `TypeError` for non-`int` values (including `bool`),
  `ValueError` for values `<= 0`.
- Propagation: `LopSfFcc._set_attributes` reads
  `command_line_arguments.parallel_threads`; `_backend_run_arguments` selects
  the run backend — serial for `1`, `multiprocessing` with `n_workers` for
  values `> 1` (warning when the count exceeds `os.cpu_count()`).

### `--md-params-json`

- Mandatory option; empty or blank values are rejected by
  `non_blank_string`.
- Constructor rejects `None` (`ValueError`); see `context.md` for the known
  as-built deviation on direct blank-string construction.
- Propagation: `LopSfFcc._set_attributes` validates the named file against
  `schemas/md_params.schema.json` via `validate_json_file`, loads it via
  `read_json_file`, and forwards the parsed parameters into the data-writer
  metadata value object so data writers can record them in the output.

### Parallel Execution Boundary (owned by the parallelization plan)

The value of `--parallel-threads` configures the selected execution backend
(e.g. `ThreadPoolExecutor`/`multiprocessing` workers); it is never accepted
and silently ignored. Future/parallel execution uses replicated data
decomposition: every worker receives the same atom coordinates, velocities,
forces, topology, and simulation metadata; each worker receives a distinct
atom-index subset, owns its accumulator exclusively, and worker-local
accumulators are merged deterministically. Thread/executor lifecycle belongs
to `LopSfFcc` or a dedicated parallel calculation layer, never to the CLI or
accumulator packages. The owning plan is
[../../../docs/LopSfFcc_parallelization_contract_plan.md](../../../docs/LopSfFcc_parallelization_contract_plan.md).

## Test Plan

All CLI contract tests live in `tests/test_lop_sf_fcc_cli_parser.py` and
verify observable command-line and public-class behavior rather than parser
implementation details:

1. Omitting `--parallel-threads` produces `parallel_threads == 1`.
2. `--parallel-threads 4` produces `parallel_threads == 4`.
3. `--parallel-threads 0`, negative, and non-integer values raise an argument
   parsing error (`SystemExit`).
4. Direct `CLILopSfFcc(parallel_threads=0)` / `-1` raise `ValueError`;
   `True` and `1.5` raise `TypeError`.
5. Omitting `--md-params-json`, or passing `""`/blanks, raises an argument
   parsing error; a valid string is accepted and stored.
6. The subparser help epilog documents `LTAT_DEBUG_PLOT_FRAMES`.
7. `LopSfFcc.__call__` can read every configured value from the CLI object
   (covered by the lop_sf_fcc feature tests).

## Non-Goals

- No thread pool, executor, or scheduling logic in the CLI layer.
- No JSON schema validation or file I/O inside the parser modules; that is
  the calculation boundary's responsibility.
- No option aliases (`--threads`, `--nthreads`) without a project-wide
  naming convention.
- No mutable exposure of CLI-class internals; properties are read-only.

## Acceptance Criteria

- `--parallel-threads` is available on the `lop_sf_fcc` subcommand, defaults
  to `1`, accepts only positive integers, and rejects invalid values both at
  the command line and at programmatic construction.
- `--md-params-json` is mandatory, rejects empty/blank values, and its file
  is validated against `md_params.schema.json` before use.
- Both values reach `LopSfFcc` and, for MD parameters, the data writers.
- All contract tests above pass, plus the full suite.

## Migration Log (Completed Work)

### `--parallel-threads` option — completed

Converted from `docs/command_line/command_line_contract_plan.md`:

- `positive_integer` parser helper added and documented.
- `parallel_threads` added to `CLILopSfFcc` with private storage, read-only
  property, and constructor-level `TypeError`/`ValueError` validation.
- `--parallel-threads` registered on the FCC subparser with default `1`.
- Value propagated to the `LopSfFcc` calculation boundary.
- Focused CLI contract tests added (items 1–4 and 7 above).
- Help text updated; no FCC CLI usage section existed in `README.md` or
  `examples/README.md` to update.
- As-built extension: subsequent parallelization work superseded the original
  "keep execution serial" step — the value now selects the run backend via
  `_backend_run_arguments` (serial for `1`, multiprocessing otherwise).

### `--md-params-json` option — completed

Converted from `docs/command_line/json_md_parameters_option_contract_plan.md`:

- Mandatory `--md-params-json` option added to the FCC subparser with the
  `non_blank_string` validator (rejects empty/blank values).
- `md_params_json` added to `CLILopSfFcc` with private storage, read-only
  property, and constructor rejection of `None`.
- Calculation boundary validates the file against
  `schemas/md_params.schema.json` (`validate_json_file`) and loads it
  (`read_json_file`) before use.
- Parsed parameters propagated to the data writers through the writer value
  object's metadata.
- Focused CLI contract tests added (item 5 above).

### Historical note

This plan was converted into an ICM feature workspace on 2026-10-04. The
original documents at `docs/command_line/command_line_contract_plan.md` and
`docs/command_line/json_md_parameters_option_contract_plan.md` are now
pointers to this file.
