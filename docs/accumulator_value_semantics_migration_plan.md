# Accumulator Value-Semantics Migration Plan

## Objective

Migrate the accumulator package from its original direct-state design to the repository's value-semantics pattern.

The migration must preserve the current worker-local accumulation behavior while separating:

- public value-object interfaces;
- concrete accumulator state;
- accumulator-specific behavior;
- immutable finalized values; and
- reduction policy.

FCC parallelization is outside the scope of this plan. The accumulator package must remain independent of worker scheduling, thread pools, process communication, and domain-specific FCC logic.

## Design Principles

- `ArrayAccumulator` remains efficient and mutable for worker-local accumulation.
- `ArrayAccumulatorValue` represents an immutable finalized snapshot.
- Concrete state owns the accumulator data; wrappers do not duplicate it.
- Accumulator-specific behavior is composed with the state rather than added to the generic value-semantics package.
- Public accessors must not expose writable internal arrays.
- Merging remains a separate reducer operation.
- Existing public accumulator behavior should remain compatible during migration.

## Class Correspondence

| Value-semantics class or protocol | Accumulator counterpart | Role |
| --- | --- | --- |
| `StateValueObjectMutable` | `ArrayAccumulator` | Public mutable wrapper used for worker-local accumulation. Delegates operations to its state and behavior. |
| `StateValueObjectImmutable` | `ArrayAccumulatorValue` | Immutable snapshot used for finalized results, reduction, and cross-worker transfer. |
| `ConcreteStateImplementation` | `ArrayAccumulatorState` | Concrete state containing `dtype`, `capacity`, `buffer`, `counters`, and `initial_value`. |
| `NumericStateImplementation` | `ArrayAccumulatorState` | Optional numeric analogue. It is not required if `ArrayAccumulatorState` directly owns NumPy-specific state. |
| `StateValueBehaviorProtocol` | `ArrayAccumulatorBehaviorProtocol` | Contract for copying, validation, replacement, updating, equality, representation, accumulation, finalization, and reset. |
| Concrete behavior implementation | `ArrayAccumulatorBehavior` | Implements accumulator-specific operations such as `accumulate`, `finalize`, and `reset`. |
| `ValueObjectInterface` | `AccumulatorValueObjectInterface` | Optional accumulator-specific interface if the generic value-object interface is insufficient. |
| `ValueSemantics` | `AccumulatorValueProtocol` | Public protocol for state-based equality and non-mutating replacement. |
| `ValueValidationError` | `AccumulatorValidationError` | Optional accumulator-specific validation exception. |
| `hash_state` | No direct counterpart | Hashing remains disabled because accumulator values contain NumPy arrays. |
| `StateValueObjectMutable.update()` | `ArrayAccumulator.accumulate()` and `reset()` | Domain-specific mutation is expressed through precise accumulator operations. |
| `StateValueObjectImmutable.replace()` | `ArrayAccumulatorValue.replace()` | Creates a new immutable accumulator value without changing the original. |

The essential mapping is:

```text
StateValueObjectMutable      -> ArrayAccumulator
StateValueObjectImmutable    -> ArrayAccumulatorValue
ConcreteStateImplementation  -> ArrayAccumulatorState
StateValueBehaviorProtocol   -> ArrayAccumulatorBehaviorProtocol
ValueSemantics               -> AccumulatorValueProtocol
```

## Target Architecture

```text
ArrayAccumulator
    mutable public wrapper
    wraps ArrayAccumulatorState
    delegates to ArrayAccumulatorBehavior

ArrayAccumulatorValue
    immutable public snapshot
    wraps immutable snapshot state
    delegates to value-specific behavior where needed

ArrayAccumulatorState
    dtype
    capacity
    buffer
    counters
    initial_value

ArrayAccumulatorBehavior
    accumulate
    finalize
    reset
    copy state
    validate state
    replace state
    update state
    compare states
    represent states

merge_accumulators
    validates compatibility
    combines values and counters
    returns a new result
```

## Concrete State Contract

`ArrayAccumulatorState` owns the following private attributes:

| Attribute | Meaning |
| --- | --- |
| `_dtype` | NumPy dtype used for buffer values. |
| `_capacity` | Number of addressable accumulator slots. |
| `_buffer` | Array containing accumulated values. |
| `_counters` | Integer array containing contribution counts per slot. |
| `_initial_value` | Coerced value used by `reset()`. |

State invariants:

- `capacity` is a positive integer;
- `buffer.shape == (capacity,)`;
- `counters.shape == (capacity,)`;
- `buffer.dtype == dtype`;
- counters use an integer dtype;
- `initial_value` is representable by `dtype`;
- buffer and counters are independently owned;
- invalid state cannot be constructed or installed through replacement.

The state may be mutable internally because it belongs to one mutable accumulator. State returned through a public property must be copied or otherwise protected from mutation.

## Common Behaviors

### `accumulate`

```python
accumulate(state, index, value) -> None
```

The behavior validates the index, coerces the value to the configured dtype, adds it to the selected buffer slot, and increments that slot's counter.

Repeated accumulation at one index remains additive.

### `finalize`

```python
finalize(state) -> np.ndarray
```

`finalize()` returns the accumulated values in public form. The migration should use a defensive copy so callers cannot modify live worker state accidentally.

`finalize()` does not replace `to_value()`. Finalization returns values for existing call sites; `to_value()` creates a complete immutable snapshot containing values and counters.

### `reset`

```python
reset(state) -> None
```

Reset restores every buffer entry to `initial_value` and clears every counter while preserving dtype and capacity.

### Value-semantics behaviors

The accumulator behavior must also provide the operations needed by the shared value-semantics wrapper:

- copy state defensively;
- validate complete state invariants;
- replace state without mutating the original value;
- update mutable state only after validating the resulting state;
- compare NumPy arrays with `np.array_equal`;
- create a useful state representation;
- reject hashing for array-containing state.

The generic `dummy_method()` is a template extension point and is not part of the accumulator design.

## Mutable Accumulator

`ArrayAccumulator` remains the compatibility-facing mutable type.

It should preserve:

- the current constructor arguments;
- `accumulate(index, value)`;
- `reset()`;
- `finalize()`;
- `capacity`;
- `dtype`;
- `name`.

It should add:

```python
to_value() -> ArrayAccumulatorValue
```

`to_value()` must copy the current buffer and counters. Later mutations of the accumulator must not affect a previously created value.

Example:

```python
accumulator.accumulate(0, 2.0)
snapshot = accumulator.to_value()
accumulator.accumulate(0, 3.0)

# snapshot remains independent of the later mutation
```

`ArrayAccumulator` must remain unhashable because its state changes after construction.

## Immutable Accumulator Value

`ArrayAccumulatorValue` represents a finalized snapshot and exposes observation only:

```python
values
counters
capacity
dtype
```

Its arrays must be defensive copies and read-only. It must not expose `accumulate()` or `reset()`.

Equality must explicitly compare:

- concrete value type;
- dtype;
- capacity;
- values using `np.array_equal`;
- counters using `np.array_equal`.

Ordinary tuple or dictionary equality must not be used for NumPy arrays.

Hashing is disabled initially:

```python
__hash__ = None
```

`replace(changes)` may be provided to satisfy the shared `ValueSemantics` protocol. Replacement must create a new validated value and leave the original unchanged.

## Reduction

Reduction remains outside both the state and wrapper classes.

The current `merge_array_accumulators` function should be retained temporarily as a compatibility API. The target reducer should operate on immutable values:

```python
merge_accumulator_values(
    left: AccumulatorValueProtocol,
    right: AccumulatorValueProtocol,
) -> ArrayAccumulatorValue
```

The reducer must:

- reject incompatible dtypes;
- reject incompatible capacities;
- avoid mutating either input;
- accept empty-but-valid values;
- add values element-wise;
- add counters element-wise;
- use a deterministic merge order when merging more than two values.

Whether legacy merging returns a mutable accumulator or an immutable value should be decided during the reducer migration phase. The long-term result should be immutable.

## Proposed Module Layout

```text
accumulator/
    __init__.py
    accumulator_protocol.py
    accumulator_value_protocol.py
    array_accumulator.py
    array_accumulator_state.py
    array_accumulator_behavior.py
    array_accumulator_value.py
    array_accumulator_value_state.py
    array_accumulator_builder.py
    array_accumulator_value_builder.py
    merge_accumulators.py
```

The behavior and state modules may be combined if they remain small and focused. The required architectural boundary is the separation between state storage, value-object wrappers, and reduction policy.

## Migration Phases

### Phase 1: Confirm the contract

Document and test:

- state fields and invariants;
- additive accumulation;
- index validation;
- reset behavior;
- finalize copy semantics;
- snapshot ownership;
- equality and hashing policy;
- merge compatibility and counter semantics.

Phase 1 deliverables are the documented state and behavior contract plus
focused tests for the currently supported accumulator behavior. The tests
cover additive global-index accumulation, dtype and capacity reporting,
capacity and index validation, reset behavior, merge compatibility, and
non-mutating merges.

Tests for defensive `finalize()` copies, immutable snapshots, read-only
snapshot arrays, value replacement, and merged counters are intentionally
deferred until the production types and behavior required by those contracts
are implemented in Phases 4 through 6.

### Phase 2: Extract concrete state

Create `ArrayAccumulatorState` and move the existing dtype, capacity, buffer, counters, and initial-value fields into it. Rename the current `_intial_value` spelling to `_initial_value`.

Keep the existing `ArrayAccumulator` constructor and public methods working.

### Phase 3: Extract accumulator behavior

Create the accumulator-specific behavior protocol and implementation. Move numerical operations and state validation into that layer while keeping domain-neutral value-semantics templates unchanged.

### Phase 4: Adapt the mutable wrapper

Make `ArrayAccumulator` delegate to the state and behavior objects. Add `to_value()` and ensure `finalize()` cannot expose writable internal storage.

### Phase 5: Implement immutable values

Create `ArrayAccumulatorValue` and its snapshot state. Add exports, protocol support, and focused tests for defensive copying, read-only arrays, equality, replacement, counters, and hashing.

### Phase 6: Migrate reduction

Add immutable-value reduction, define counter merge behavior, and retain the current reducer as a compatibility layer until callers have migrated.

### Phase 7: Migrate builders and documentation

Update builders to construct independent mutable accumulators and immutable values. Update package exports and accumulator documentation to describe the new ownership boundaries.

## Testing Plan

Add focused accumulator tests for:

1. state construction and invariant validation;
2. additive accumulation and value coercion;
3. invalid and out-of-range indices;
4. reset restoring the initial value and clearing counters;
5. `finalize()` not exposing writable internal state;
6. `to_value()` producing an independent snapshot;
7. snapshot arrays being read-only;
8. snapshot equality using array contents;
9. replacement leaving the original snapshot unchanged;
10. hashing being disabled;
11. merging values without mutating inputs;
12. dtype and capacity incompatibility errors;
13. counter preservation and counter merging;
14. independent builder-created accumulators.

Run focused accumulator tests first, followed by the complete pytest suite.

## Open Decisions

The following decisions should be finalized before implementation begins:

- Should `finalize()` return a defensive copy or a read-only view? The recommended choice is a defensive copy for maximum compatibility safety.
- Should `ArrayAccumulatorValue` use a separate immutable state class? The recommended choice is yes if mutable and immutable invariants differ; otherwise a shared state representation may be sufficient.
- Should `replace()` accept a mapping of field changes or a domain-specific typed value? A mapping matches the current generic template, but a typed replacement API may provide stronger validation.
- Should counters be included in equality and reduction? The recommended choice is yes because they describe the accumulation state and are needed for later normalization.
- Should legacy `merge_array_accumulators` return a mutable accumulator during transition? This can preserve compatibility, while the new immutable reducer becomes the long-term API.
- Should `name` be part of value equality? The recommended choice is no if it is descriptive metadata rather than numerical state.

## Non-Goals

- Adding thread safety or worker scheduling to accumulators.
- Coupling accumulator state to FCC, MDAnalysis, or trajectory objects.
- Adding sparse storage before dense storage is validated and profiled.
- Modifying the generic value-semantics template to contain accumulator-specific behavior.
- Introducing hashing for NumPy-array-backed values.
