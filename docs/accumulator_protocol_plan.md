# Accumulator Protocol Plan

## Objective

Define a domain-neutral protocol for thread-local accumulators and prepare the accumulator package for parallel trajectory calculations.

The long-term calculation model uses replicated data decomposition:

- Every worker receives the same atom coordinates, velocities, forces, topology, and simulation metadata.
- Each worker calculates a property for a subset of atom indices.
- Each worker stores its local results in an independent accumulator.
- A coordinator merges the worker accumulators into one final result.

The first target calculation is a local order parameter for FCC structure factors.

## Mutability Decision

The accumulator design has two possible models:

### Immutable-only accumulator

An immutable accumulator would return a new object after every accumulation.
This provides strong value semantics and safe cross-thread sharing, but it is
not appropriate for the worker hot loop because repeated array updates would
create unnecessary allocations and copies.

### Mutable-only accumulator

A mutable accumulator is efficient for worker-local updates, but its state can
change while another layer is reading or reducing it. That makes ownership and
snapshot boundaries harder to enforce.

### Selected design: mutable worker plus immutable value

Use two related objects:

```text
ArrayAccumulator
    mutable, worker-local accumulation buffer

ArrayAccumulatorValue
    immutable snapshot of finalized values and counters
```

`ArrayAccumulator` remains mutable and is never shared between workers.
`ArrayAccumulator.to_value()` creates an independent immutable snapshot.
Reduction and cross-worker handoff should operate on immutable values wherever
possible:

```text
worker-local ArrayAccumulator
    -> to_value()
    -> immutable ArrayAccumulatorValue
    -> deterministic reduction
    -> final immutable result
```

This preserves efficient accumulation while giving the parallel reduction
layer explicit immutable value semantics.

## Architectural Boundaries

Keep the responsibilities separate:

```text
calculation layer
    owns atom partitioning and worker execution

accumulator
    owns local value storage, indexing, validation, and finalization

reducer
    owns compatibility checks and accumulator merging

builder
    creates correctly configured independent accumulators
```

The accumulator must not own thread pools, locks, process communication, MPI behavior, or worker scheduling. This keeps the protocol usable with threads, multiprocessing, joblib, Dask, MPI, or future GPU workers.

## Proposed Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    accumulator/
      __init__.py
      accumulator_protocol.py
            accumulator_value_protocol.py
      array_accumulator.py
            array_accumulator_value.py
      accumulator_reducer.py
      array_accumulator_builder.py
            array_accumulator_value_builder.py
```

The existing `merge_accumulators.py` may remain as the initial reducer module, or be renamed to `accumulator_reducer.py` when the generic protocol-based reducer is introduced.

## Protocol Contract

Add `accumulator_protocol.py` with a small protocol describing thread-local accumulation and finalization:

```python
from typing import Any, Protocol, Self, TypeVar

T = TypeVar("T")


class AccumulatorProtocol(Protocol[T]):
    """Protocol for mutable worker-local accumulation."""

    def accumulate(self, index: int, value: T) -> None:
        """Add a value associated with an atom or result index."""
        ...

    def finalize(self) -> Any:
        """Return the current accumulated result in public form."""
        ...

    def reset(self) -> None:
        """Clear accumulated values while preserving configuration."""
        ...

    @property
    def capacity(self) -> int:
        """Return the number of addressable result slots."""
        ...

    @property
    def dtype(self) -> Any:
        """Return the stored value type."""
        ...
```

Use more precise NumPy typing when the supported Python and NumPy versions make that practical. Avoid placing domain-specific concepts such as FCC structure factors, atom coordinates, or MDAnalysis objects in the protocol.

## Accumulation Semantics

- `index` represents the global atom or property index, not a worker-local loop counter.
- Repeated accumulation at one index is additive unless a separate accumulation operation is explicitly introduced.
- Every worker owns its accumulator exclusively during local calculation.
- `ArrayAccumulator` does not need to be internally thread-safe under this ownership model.
- An accumulator may be reset and reused only after the previous result has been finalized or discarded.
- The accumulator stores calculated properties, not coordinates, velocities, forces, or topology.

## Merge Semantics

Define merge behavior explicitly before adapting `ArrayAccumulator`:

- Inputs must have compatible dtypes.
- Inputs must have compatible capacities, or the padding rule must be documented.
- Merging must not mutate either source accumulator.
- Empty accumulators must be valid merge inputs.
- Duplicate global indices must follow the same additive semantics as local accumulation.
- The reducer must validate frame, timestep, operation, shape, and unit metadata if those fields are introduced.
- Merge order must be deterministic when reproducible floating-point results are required.

Floating-point addition is not associative. Use a fixed worker order or fixed reduction-tree order for reproducible results. Compensated summation can be added later if numerical error becomes significant.

Initially, keep merging as a separate reducer function rather than forcing it into the accumulator class. This separates storage behavior from reduction policy:

```python
def merge_accumulators(
    left: AccumulatorProtocol[T],
    right: AccumulatorProtocol[T],
) -> AccumulatorProtocol[T]:
    ...
```

The reducer should accept protocol-compatible accumulators rather than only `ArrayAccumulator`.

Add a separate immutable value protocol for finalized snapshots:

```python
class AccumulatorValueProtocol(Protocol[T]):
    """Protocol for immutable finalized accumulator values."""

    @property
    def values(self) -> Any:
        """Return read-only accumulated values."""
        ...

    @property
    def counters(self) -> Any:
        """Return read-only contribution counts."""
        ...

    @property
    def capacity(self) -> int:
        """Return the global result capacity."""
        ...

    @property
    def dtype(self) -> Any:
        """Return the stored value dtype."""
        ...
```

`ArrayAccumulatorValue` should implement both `AccumulatorValueProtocol` and
the repository's `ValueSemantics` protocol. Its state must use defensive
copies and read-only NumPy arrays. Equality should use `np.array_equal`; raw
NumPy array comparison must not be delegated to ordinary dictionary equality.
Hashing should remain disabled initially because NumPy arrays are unhashable.

## Phase 1 Contract Decisions

Phase 1 establishes the following decisions for the protocol implementation:

1. **Merging remains a separate reducer operation.**

    `AccumulatorProtocol` describes local accumulation, reset, finalization,
    capacity, and dtype. It does not require a `merge` method. A separate
    reducer can combine different accumulator implementations without adding
    reduction policy to the storage object.

2. **The initial storage model is dense and globally indexed.**

    Every worker accumulator uses the same global capacity and accepts global
    atom or property indices. The protocol-level reducer will reject different
    capacities because a mismatch indicates incompatible replicated-domain
    configuration. The existing padding behavior in
    `merge_array_accumulators` is legacy behavior and should be reviewed during
    Phase 3 before it is retained or replaced.

3. **An empty accumulator is valid.**

    Empty means that no values have been accumulated yet; it does not mean that
    the accumulator has zero capacity. A valid accumulator still has a positive
    configured capacity and compatible dtype.

4. **Accumulation is additive and local.**

    Repeated writes to one global index add values. Each worker exclusively owns
    its accumulator during calculation, so the protocol does not require locks
    or thread-safe mutation. Parallel scheduling and atom-index partitioning
    remain outside the accumulator package.

5. **Reduction order is deterministic.**

    The coordinator must merge worker accumulators in ascending worker or
    partition order, or use a documented fixed reduction tree. This provides
    reproducible results within the limits of floating-point arithmetic.

6. **Metadata is outside the initial protocol.**

    The first protocol contains no frame, timestep, units, operation, or worker
    identity fields. A later metadata contract may be added when the FCC
    calculation demonstrates a need for cross-worker compatibility validation.

7. **Typing is portable at the protocol boundary.**

    The protocol will use a generic value type and `Any` for the initial
    finalized result. Concrete implementations may use NumPy arrays and
    `np.dtype`; more precise NumPy typing can be introduced during Phase 2 or 3
    without coupling the protocol to FCC or MDAnalysis types.

## Dense And Sparse Storage

Consider two storage strategies:

### Dense storage

Dense storage is the default initial implementation. Every worker and every global result index is represented explicitly in an array of fixed capacity. This is efficient for repeated additive accumulation in fixed-size local-property calculations and matches the initial FCC local-order use case well.

Benefits:

- predictable memory layout
- direct indexing by global atom index
- easy validation for capacity and dtype compatibility
- simple deterministic reduction semantics

Costs:

- memory grows with the configured global capacity
- sparse domains waste space when many indices are unused
- some calculations may compute only a small subset of atoms or properties

### Sparse storage

Sparse storage permits only populated indices to be tracked and is useful when the domain is large but the actual touched indices are small. This reduces memory when local calculations are limited to a subset of atoms or properties.

Benefits:

- lower memory use in sparse domains
- natural fit for irregular local property calculations

Costs:

- more complex indexing and validation rules
- more complicated reducer semantics
- less straightforward determinism guarantees when merging partial sparse maps

### Decision

Start with dense storage for Phase 1. Keep the protocol abstract enough to support sparse implementations later if the workload or memory profile warrants it.

## Implementation Notes

The canonical implementation should keep the following responsibilities clear:

- `ArrayAccumulator` owns local mutable accumulation state.
- `ArrayAccumulatorValue` owns immutable snapshot state.
- `merge_accumulators` owns reduction semantics.
- builders own construction policy and configuration validation.

The dense accumulator should remain independent of the FCC calculation itself and should not embed trajectory or atom metadata in the storage contract.

## Phase 2 and Beyond

After the dense implementation is stabilized, extend the protocol with more explicit metadata and compatibility validation only when there is demonstrated need. Candidate additions include:

- frame or timestep metadata
- worker identity or partition metadata
- units or normalization fields
- sparse-capacity or occupancy metadata
- specialized reducer factories for exact reproducibility

This keeps Phase 1 focused on the essential storage and reduction contract without prematurely overfitting the accumulator design to a single domain-specific calculation.

### Dense replicated accumulator

Each worker stores an array sized for the global atom or property count.

Advantages:

- simple global indexing;
- fast accumulation;
- straightforward merging;
- predictable memory layout.

Disadvantage:

- memory scales with `number_of_workers * number_of_atoms * property_size`.

### Sparse local accumulator

Each worker stores only the indices it computes.

Advantages:

- lower memory use when worker subsets are small;
- less storage for sparse calculations.

Disadvantages:

- more complicated merging;
- additional indexing overhead;
- more validation requirements.

Use dense storage for the initial FCC local order-parameter calculation. Revisit sparse storage only after profiling demonstrates a memory problem.

## Metadata

The initial protocol should remain small. If the calculation requires metadata, keep it separate from the numerical storage where possible:

```text
AccumulatorProtocol
    values, indexing, merge compatibility, and finalization

AccumulationMetadata
    frame, timestep, units, operation identity, and global shape
```

Potential metadata includes:

- global atom count;
- property shape;
- dtype;
- operation name;
- frame or timestep identifier;
- number of contributions per index;
- units;
- completion status.

Do not store worker IDs unless they are needed for diagnostics or deterministic reduction.

## ArrayAccumulator Migration

Adapt `ArrayAccumulator` to satisfy the mutable `AccumulatorProtocol` without
changing its existing public behavior.

Preserve:

- `accumulate`;
- `reset`;
- `finalize`;
- `capacity`;
- `dtype`;
- current validation and value-coercion behavior.

Add:

- `to_value() -> ArrayAccumulatorValue` for immutable snapshots;
- defensive copying at the snapshot boundary;
- no sharing of mutable worker state across workers.

Keep reduction as a separate operation over immutable values rather than
adding merge policy to the mutable worker object.

## Builder Integration

Create an `ArrayAccumulatorBuilder` using the shared design-pattern builder template. The builder must create a fresh accumulator for each worker:

```python
builder(dtype=np.complex64, capacity=number_of_atoms)
```

The parallel calculation layer must never share one mutable accumulator between workers. The builder should produce independent instances with the requested dtype, capacity, initial value, and optional name or metadata.

The builder should satisfy the existing `SupportsBuild` protocol and be registered through `BuilderRegistry` if a registry is needed for multiple accumulator implementations.

Also create an `ArrayAccumulatorValueBuilder` for immutable finalized values.
Both builders must be registered in domain-owned `BuilderRegistry` instances.

## Parallel Calculation Sequence

The target execution flow is:

```text
prepare replicated atom data
create one accumulator per worker
partition global atom indices
calculate the local FCC property for assigned indices
accumulate into the worker-local accumulator
reduce accumulators in deterministic order
finalize the global result
```

The partitioning and execution mechanism belongs outside the accumulator package. The accumulator only receives global indices and calculated values.

## Implementation Phases

### Phase 1: Confirm the contract

- **Completed:** Keep merging as a separate reducer function.
- **Completed:** Use dense, globally indexed accumulators with equal capacities
    for protocol-level reduction; empty accumulators remain valid.
- **Completed:** Reduce workers in a deterministic order.
- **Completed:** Rely on exclusive worker ownership instead of internal locks.
- **Completed:** Use generic protocol typing with an initially portable
    finalized-result type and NumPy-specific typing in concrete implementations.
- Defer frame, timestep, units, operation, and other metadata compatibility
    rules until a concrete calculation requires them.

### Phase 2: Add the protocol

- Create `accumulator_protocol.py`.
- Export `AccumulatorProtocol` from `accumulator/__init__.py`.
- Define `AccumulatorValueProtocol` for immutable finalized values.
- Keep the protocol independent of trajectory, analysis, writer, HDF5, and MDAnalysis modules.

### Phase 3: Adapt the existing implementation

- Make `ArrayAccumulator` satisfy the protocol.
- Preserve its current public API and storage semantics.
- Add `ArrayAccumulatorValue` using the value-semantics templates.
- Add `ArrayAccumulator.to_value()` with defensive array copies.
- Refine merge logic to operate on protocol-compatible accumulators.
- Keep domain-specific calculation code out of the accumulator package.

### Phase 4: Add builder support

- **Completed:** Create and export `ArrayAccumulatorBuilder` using the shared
    direct-callable builder contract.
- **Completed:** Ensure each build call returns an independent accumulator.
- **Completed:** Register `ArrayAccumulatorBuilder` in the domain-owned
    `array_accumulator_builder_registry`, even though the package currently has
    one accumulator implementation.

### Phase 5: Integrate the FCC calculation

- Identify the global atom-index partitioning boundary.
- Construct one accumulator per worker.
- Accumulate local FCC properties using global indices.
- Merge worker results deterministically.
- Finalize only after reduction completes.

### Phase 6: Evaluate performance and storage

- Measure accumulator allocation, local accumulation, and merge costs.
- Measure memory usage for dense replicated storage.
- Consider sparse storage or tree reduction only if profiling demonstrates a need.
- Evaluate numerical reproducibility across worker counts and merge orders.

## Acceptance Criteria

- `AccumulatorProtocol` is domain-neutral and has a documented public contract.
- `ArrayAccumulator` satisfies the mutable worker-local protocol without an
    unnecessary API break.
- `ArrayAccumulatorValue` satisfies the immutable value protocol and the
    repository's value-semantics contract.
- Snapshot arrays are defensively copied and read-only.
- `ArrayAccumulator.to_value()` produces a value independent of later worker
    mutations.
- Independent accumulators can be created for each worker.
- Worker-local accumulation requires no shared mutable state or locks.
- Protocol-compatible accumulator results can be merged without mutating inputs.
- Merge compatibility and deterministic-order policies are documented.
- The FCC calculation can use global atom indices with replicated input data.
- Accumulator construction follows the shared builder template.
- The design does not depend on a specific parallel execution backend.
