# LopSfFcc Parallelization Contract Plan

## Objective

Prepare `LopSfFcc.__call__` for parallel execution of:

- `calculate_sf_fcc_atom_order_parameter_no_coeffs`;
- `calculate_sf_fcc_atom_order_parameter_with_coeffs`.

Each thread must receive an immutable assignment of global atom indices. A
thread is allowed to receive no atoms. The required ownership invariant is
that every atom index belongs to one and only one thread.

No files are modified by this planning task. This document defines the
contract for the later implementation.

## Atom Assignment Contract

Represent the assignment as an immutable collection:

```text
thread 0 -> (atom_index, atom_index, ...)
thread 1 -> (atom_index, atom_index, ...)
...
```

Recommended representation:

```python
tuple[np.ndarray, ...]
```

The outer tuple contains one entry for every configured thread. Each inner
array is a one-dimensional NumPy array containing the global atom indices
assigned to that thread. Each array must use an integer dtype and have
`arr.flags.writeable is False`.

The assignment object should expose read-only operations such as:

```python
thread_count
atom_count
atoms_for_thread(thread_index)
assignments
```

Do not expose mutable lists or writable NumPy arrays.

Each thread assignment array should be constructed as a defensive copy,
validated, and then made read-only:

```python
thread_atoms = np.asarray(indices, dtype=np.int64).copy()
thread_atoms.flags.writeable = False
```

The assignment object should return read-only arrays through its public API;
callers must not receive writable views.

## Required Ownership Invariants

For `atom_count = N` and `thread_count = T`:

- There are exactly `T` thread assignment entries.
- `thread_count` must be positive.
- `atom_count` may be zero.
- Each atom index is an integer in `[0, N)`.
- Every atom index in `[0, N)` appears exactly once overall.
- No atom index is assigned to more than one thread.
- A thread assignment may be empty.
- `thread_count` may be greater than `atom_count`.
- Assignment order is deterministic.

The central invariant is:

```text
union of all thread assignments = {0, 1, ..., atom_count - 1}
```

and the assignments are pairwise disjoint.

Examples:

```text
3 atoms, 5 threads:
thread 0 -> (0,)
thread 1 -> (1,)
thread 2 -> (2,)
thread 3 -> ()
thread 4 -> ()
```

```text
6 atoms, 3 threads:
thread 0 -> (0, 1)
thread 1 -> (2, 3)
thread 2 -> (4, 5)
```

The implementation must not require every thread to contain an atom.

## Validation

Validate assignments when they are constructed. Conceptually:

```python
flattened = tuple(
    atom_index
    for thread_atoms in assignments
    for atom_index in thread_atoms
)

if len(assignments) != thread_count:
    raise ValueError("assignment count must equal thread count")

if len(flattened) != atom_count:
    raise ValueError("each atom must have exactly one assignment")

if len(set(flattened)) != atom_count:
    raise ValueError("an atom index is assigned to multiple threads")

if set(flattened) != set(range(atom_count)):
    raise ValueError("atom assignments must cover every atom index")
```

Also reject:

- non-positive thread counts;
- negative atom counts;
- non-integer atom indices;
- indices outside the global atom range;
- mutable internal state exposed through public accessors.

The constructor should defensively copy incoming sequences into NumPy 1D
arrays before validation and storage. Every stored array must be read-only.

## Assignment Protocols

Assignment value objects should share a common read-only protocol so the FCC
calculation layer depends on behavior rather than one concrete implementation.

### `AtomAssignmentProtocol`

Use this as the primary protocol:

```python
import numpy as np
from typing import Protocol


class AtomAssignmentProtocol(Protocol):
    """Read-only ownership mapping from threads to atom indices."""

    @property
    def thread_count(self) -> int:
        """Return the number of thread assignments."""
        ...

    @property
    def atom_count(self) -> int:
        """Return the total number of atoms."""
        ...

    @property
    def assignments(self) -> tuple[np.ndarray, ...]:
        """Return read-only 1D assignments ordered by thread index."""
        ...

    def atoms_for_thread(self, thread_index: int) -> np.ndarray:
        """Return a read-only 1D array assigned to one thread."""
        ...

    def owner_of_atom(self, atom_index: int) -> int:
        """Return the unique owning thread for an atom."""
        ...
```

The protocol describes read-only behavior. Runtime immutability must be
provided by the concrete implementation using read-only NumPy arrays and an
outer immutable tuple.

### `ImmutableValueProtocol`

If multiple assignment value objects need common value semantics, define a
small reusable protocol for validation and non-mutating replacement:

```python
from typing import Protocol, Self


class ImmutableValueProtocol(Protocol):
    """Protocol for immutable value objects."""

    def validate(self) -> None:
        """Validate the complete value state."""
        ...

    def replace(self, **changes: object) -> Self:
        """Return a new value with selected fields replaced."""
        ...
```

This protocol is optional for the first implementation. `AtomAssignmentProtocol`
is the required domain-facing contract.

### `AtomAssignmentFactoryProtocol`

Keep partition construction separate from the assignment value when multiple
partitioning strategies may be introduced:

```python
class AtomAssignmentFactoryProtocol(Protocol):
    """Protocol for deterministic atom-assignment factories."""

    def create(
        self,
        atom_count: int,
        thread_count: int,
    ) -> AtomAssignmentProtocol:
        """Create a validated immutable atom assignment."""
        ...
```

The first factory should provide deterministic contiguous balanced
partitioning. Future strategies may include round-robin, spatial, or
workload-weighted partitioning without changing the consumer contract.

## Assignment Builder

The concrete assignment implementation should have a builder following the
shared `design_patterns_templates` builder pattern:

```text
AtomThreadAssignmentBuilder
```

The builder creates new immutable values and never mutates an existing
assignment:

```python
assignment = builder(atom_count=10, thread_count=3)
```

It should satisfy `SupportsBuild` and may be registered with `BuilderRegistry`
if more than one assignment implementation requires keyed lookup. A global
registry is unnecessary while there is only one implementation.

Recommended initial public types:

```text
AtomAssignmentProtocol
AtomThreadAssignment
AtomThreadAssignmentBuilder
```

The calculation layer should depend on `AtomAssignmentProtocol`, while the
builder and concrete value object remain responsible for construction and
validation.

## Partitioning Policy

Use deterministic contiguous balanced partitioning initially. For `N` atoms
and `T` threads, distribute the remainder consistently among the first
threads while preserving global index order.

The policy must allow empty assignments when `T > N`:

```text
N = 2, T = 4
thread 0 -> (0,)
thread 1 -> (1,)
thread 2 -> ()
thread 3 -> ()
```

Round-robin partitioning may be evaluated later, but the first implementation
should use one documented deterministic policy.

## Storage On `LopSfFcc`

In `LopSfFcc.__call__`:

1. Read `command_line_arguments.parallel_threads`.
2. Load the universe and determine `nm_atoms`.
3. Construct the immutable atom assignment.
4. Store it in private state, for example:

```python
self._atom_thread_assignment = AtomThreadAssignment.from_balanced_partition(
    atom_count=nm_atoms,
    thread_count=self._parallel_threads,
)
```

Expose a read-only property only if external inspection is needed. Do not allow
calculation functions or worker code to replace or mutate the assignment.

## Function Interfaces

The calculation functions should eventually receive read-only atom-index
assignments:

```python
def calculate_sf_fcc_atom_order_parameter_no_coeffs(
    universe: MDA_Universe,
    wave_vectors: LatticeVectors,
    cutoff: float,
    atom_indices: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    ...
```

```python
def calculate_sf_fcc_atom_order_parameter_with_coeffs(
    nm_atoms: int,
    nm_wavevectors: int,
    accum_lop_terms_no_coeffs: np.ndarray,
    accum_lop_nm_neighbors: np.ndarray,
    atom_indices: Sequence[int],
) -> np.ndarray:
    ...
```

Treat `atom_indices` as read-only. A tuple is preferred over a mutable list.

During migration, an optional `None` value may temporarily represent the
serial all-atom path. Once all callers use explicit assignments, make the
argument required.

## Pair Contribution Ownership

The no-coefficients function currently loops over atom pairs and contributes to
both endpoints. Atom ownership must be respected when this loop is
parallelized.

Recommended rule:

- Workers may read the complete pair list and shared atom data.
- A worker may write only result slots for its assigned atoms.
- For each pair `(atom_i, atom_j)`, update `atom_i` only if it belongs to the
  current worker.
- Update `atom_j` only if it belongs to the current worker.

Conceptually:

```python
if atom_i in assigned_atoms:
    update_result_for_atom_i()

if atom_j in assigned_atoms:
    update_result_for_atom_j()
```

Do not assign each pair to only one worker without proving that both endpoint
contributions remain correct.

## Result Ownership And Accumulators

Use one independent accumulator per thread. The accumulator should use global
capacity and global atom indices, while each worker writes only its assigned
indices.

Required rules:

- A worker owns its accumulator exclusively during calculation.
- No worker writes to another worker's accumulator.
- Shared coordinates, velocities, forces, topology, and pair data are read-only.
- Worker accumulators are merged only after all workers finish.
- Results are merged in deterministic thread-index order.
- Empty thread assignments produce valid empty local contributions and do not
  invalidate the reduction.

Dense per-thread accumulators are recommended initially because they preserve
simple global indexing and fit the current accumulator contract. Sparse local
results can be evaluated later if memory profiling justifies the complexity.

## Execution Separation

The assignment object describes ownership only. It must not:

- create threads;
- start executors;
- calculate FCC properties;
- own atom coordinates or simulation data;
- mutate calculation results;
- perform accumulator reduction.

`LopSfFcc` or a dedicated parallel calculation layer owns worker scheduling,
while the accumulator package owns local result storage and the reducer owns
merging.

## Implementation Phases

### Phase 1: Define the assignment value object

- Create an immutable assignment type.
- Add deterministic balanced partition construction.
- Allow empty thread assignments.
- Validate exact, disjoint, complete atom coverage.
- Expose only read-only NumPy 1D arrays inside an immutable outer tuple.

### Phase 2: Integrate assignment creation

- Read the configured thread count in `LopSfFcc.__call__`.
- Create the assignment after `nm_atoms` is known.
- Store it privately on `LopSfFcc`.
- Keep the existing serial calculation behavior unchanged.

### Phase 3: Add assignment-aware function inputs

- Add read-only atom-index arguments to both FCC calculation functions.
- Update loops to calculate or write only assigned atom indices.
- Preserve a temporary serial compatibility path if required.
- Confirm pair endpoint contributions remain correct.

### Phase 4: Add worker execution

- Create one accumulator per thread.
- Pass each immutable assignment to its worker.
- Execute workers using the configured thread count.
- Ensure shared input data remains read-only.

### Phase 5: Reduce and finalize

- Merge worker-local results in deterministic thread-index order.
- Support empty worker assignments.
- Finalize the global FCC result only after reduction completes.
- Compare serial and parallel results for equivalent input.

### Phase 6: Profile and optimize

- Measure partitioning, worker execution, accumulator allocation, and merge
  costs.
- Measure memory use for dense per-thread storage.
- Consider sparse storage or a fixed reduction tree only if profiling requires
  it.

## Acceptance Criteria

- The assignment has exactly one entry per configured thread.
- Empty thread assignments are valid.
- Every atom index is assigned to exactly one thread.
- No atom index is duplicated across threads.
- All atom assignments are immutable after construction.
- Assignment order is deterministic.
- The assignment can be stored by `LopSfFcc` and passed to both FCC calculation
  functions.
- Workers cannot mutate their own or another worker's atom assignment.
- Workers write only to their own assigned result indices and accumulators.
- Shared atom data is read-only during calculation.
- Empty workers can participate in reduction without special ownership errors.
- Parallel reduction produces the same atom ownership semantics as serial
  execution.
