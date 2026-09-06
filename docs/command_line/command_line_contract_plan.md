# Command Line Contract Plan

## Task

### Setting the Number of Parallel Threads

Add a command-line option for configuring the number of parallel threads used by the FCC calculation.

The option must:

- default to `1`;
- accept only positive integers;
- raise an error for zero, negative, or non-integer values;
- store the validated value in the FCC CLI class;
- make the value available to the calculation layer for future parallel execution.

The current CLI class is named `CLILopSfFcc`, not `CLILopFcc`. Keep the existing class name unless a separate rename is explicitly required.

## CLI Option

Add the following option to the FCC subparser in
`lop_sf_fcc_cli_parser.py`:

```text
--parallel-threads
```

Recommended destination and property name:

```text
parallel_threads
```

Example:

```bash
lammps_analysis_tool lop_sf_fcc \
    --trajectory trajectory.dcd \
    --psf topology.psf \
    --edge-length 5.26 \
    --timeunits ps \
    --dt 0.01 \
    --cutoff 4.5 \
    --parallel-threads 4
```

Use `default=1` and a dedicated positive-integer parser:

```python
def positive_integer(value: str) -> int:
    """Parse a strictly positive integer."""
    parsed_value = int(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "parallel thread count must be a positive integer"
        )
    return parsed_value
```

Register the option with:

```python
parser1.add_argument(
    "--parallel-threads",
    type=positive_integer,
    default=1,
    help="Number of parallel threads. (default: %(default)s)",
)
```

`argparse` should reject invalid command-line values before the calculation starts.

## CLI Class Contract

Add `parallel_threads` to `CLILopSfFcc`:

```python
parallel_threads: int = 1
```

Store it privately:

```python
self._parallel_threads = parallel_threads
```

Expose it through a property:

```python
@property
def parallel_threads(self) -> int:
    """Return the configured number of parallel threads."""
    return self._parallel_threads
```

Validate the value in the class constructor as well as in the command-line parser. The class can be instantiated directly without going through `argparse`, so it must reject invalid values independently.

Recommended constructor validation:

```python
if parallel_threads <= 0:
    raise ValueError("parallel_threads must be a positive integer")
```

Direct construction should also reject non-integer values rather than silently coercing them.

## Naming

Use `parallel_threads` for the internal field and public property.

Use `--parallel-threads` as the initial command-line spelling. Do not add `--threads` or `--nthreads` unless an existing project-wide naming convention requires an alias.

## Propagation To `LopSfFcc`

The current calculation entry point is `LopSfFcc.__call__`, which receives a `CLILopSfFcc` instance. Read the configured value from the CLI object at the calculation boundary:

```python
parallel_threads = command_line_arguments.parallel_threads
```

For the initial change, establish the configuration data flow without introducing a thread pool. The current calculation remains serial until the parallel execution phase is implemented.

The value must not be accepted and silently ignored once parallel execution is introduced. It should configure the selected execution backend, for example:

```python
ThreadPoolExecutor(max_workers=parallel_threads)
```

## Parallel Execution Boundary

Future execution should use replicated data decomposition:

```text
read parallel_threads from the CLI configuration
load replicated atom data
partition global atom indices into parallel_threads subsets
create one accumulator per worker
calculate local FCC properties for each subset
merge worker-local accumulators deterministically
finalize the global result
```

All workers receive the same atom coordinates, velocities, forces, topology, and simulation metadata. Each worker receives a distinct atom-index subset and owns its accumulator exclusively.

Thread creation, scheduling, and executor lifecycle belong to `LopSfFcc` or a dedicated parallel calculation layer. They do not belong in the accumulator package.

## Testing Plan

Add focused tests for the CLI contract:

1. Omitting the option produces `parallel_threads == 1`.
2. `--parallel-threads 4` produces `parallel_threads == 4`.
3. `--parallel-threads 0` raises an argument parsing error.
4. Negative values raise an argument parsing error.
5. Non-integer values raise an argument parsing error.
6. Direct construction of `CLILopSfFcc(parallel_threads=0)` raises `ValueError`.
7. Direct construction with a non-integer value is rejected.
8. `LopSfFcc.__call__` can read the configured value from the CLI object.

Tests should verify observable command-line and public-class behavior rather than parser implementation details.

## Documentation Updates

Update the relevant CLI documentation, including:

- `README.md`;
- `examples/README.md`;
- the FCC CLI parser help text;
- this plan or the project plan if the setting becomes a project-wide configuration rule.

Document:

```text
--parallel-threads INTEGER
Default: 1
Requirement: positive integer
```

## Implementation Sequence

1. **Completed:** Add and document the positive-integer parsing helper.
2. **Completed:** Add `parallel_threads` to `CLILopSfFcc` with private storage
    and a property.
3. **Completed:** Add constructor-level validation for programmatic CLI
    construction.
4. **Completed:** Register `--parallel-threads` on the FCC subparser with
    default `1`.
5. **Completed:** Propagate the value to the `LopSfFcc` calculation boundary.
6. **Completed:** Keep execution serial until the parallel backend phase is
    implemented.
7. **Completed:** Add focused CLI contract tests.
8. **Completed:** Update the FCC parser help text; no existing FCC CLI usage
    section was present in `README.md` or `examples/README.md`.
9. **Completed:** Run focused tests, FCC tests, and the complete test suite.

## Acceptance Criteria

- `--parallel-threads` is available on the FCC subcommand.
- Its default value is `1`.
- Only positive integers are accepted.
- Invalid command-line values produce an `argparse` error.
- Programmatic `CLILopSfFcc` construction also rejects invalid values.
- `CLILopSfFcc.parallel_threads` exposes the validated value.
- The value reaches `LopSfFcc`.
- No thread pool is introduced before the parallel execution phase.
- The future design supports one accumulator per worker and deterministic merging.
