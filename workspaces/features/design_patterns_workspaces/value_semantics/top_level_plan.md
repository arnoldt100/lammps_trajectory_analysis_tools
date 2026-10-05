# Top Level Plan - Value Semantics

This is the canonical standing plan for the value-semantics template feature.
It inherits all project-wide rules from
[../../../top_level_plan.md](../../../top_level_plan.md) and the
collection-level rules from
[../top_level_plan.md](../top_level_plan.md); it must not weaken either level.

## Objective

Maintain a reusable, domain-neutral value-semantics template package under
`design_patterns_templates/value_semantics/`, based on value-oriented design
principles:

- objects are defined by their state rather than identity;
- equal state produces equal values;
- copies are independent unless sharing is explicit and documented;
- invariants are established at construction or controlled update boundaries;
- operations are predictable, composable, and easy to test.

## Package Structure (As Built)

```text
src/
  lammps_trajectory_analysis_tools/
    design_patterns_templates/
      value_semantics/
        __init__.py
        protocols.py
        value_object_interface.py
        state_value_object_immutable.py
        state_value_object_mutable.py
        value_object_behaviors.py
        validation.py
        concrete_state_implementation.py
        concrete_state_implementation_helpers.py
        numeric_state_implementation.py

tests/
  design_patterns_templates/
    value_semantics/
      test_value_object.py
      test_value_object_behaviors.py
      test_validation.py

workspaces/
  features/
    design_patterns_workspaces/
      value_semantics/
        README.md
        context.md
        top_level_plan.md
```

### Public API

| Module | Public names |
| --- | --- |
| `protocols.py` | `StateValueBehaviorProtocol`, `ValueSemantics` (runtime-checkable) |
| `value_object_interface.py` | `ValueObjectInterface` (ABC, `__slots__ = ()`, no state) |
| `state_value_object_immutable.py` | `StateValueObjectImmutable` |
| `state_value_object_mutable.py` | `StateValueObjectMutable` |
| `value_object_behaviors.py` | `hash_state`, `invoke_dummy_method`, `StateValueObject` union |
| `validation.py` | `ValueValidationError`, `validate_state` |
| `concrete_state_implementation.py` | `ConcreteStateImplementation` (example) |
| `numeric_state_implementation.py` | `NumericStateImplementation` (example) |

`__init__.py` exports all of the above except the helpers module internals;
`design_patterns_templates/__init__.py` re-exports the two wrapper types.

## Design Rules

- Keep every class-level and instance-level data attribute private with a
  single leading underscore; expose required external access through
  properties.
- Keep templates domain-neutral. They must not import trajectory, analysis,
  writer, HDF5, or MDAnalysis modules.
- Prefer composition and small protocols over inheritance-heavy frameworks.
- Make value state explicit and inspectable.
- Define equality from value state, not object identity.
- Ensure hashing is available only when the value is immutable and all
  participating fields are hashable.
- Make copying behavior explicit, especially for mutable nested values.
- Validate invariants at construction and at every public mutation boundary.
- Avoid hidden global state, registries, singletons, and backend resources in
  value templates.
- Keep algorithms that operate on values separate from the value object where
  that improves reuse.
- Use type annotations and precise docstrings for the intended extension
  points.
- Keep the templates small enough that a domain implementation can understand
  and adapt them rather than inherit accidental policy.

## Behavior-Delegation Contract (Finalized)

The templates own their state and delegate state operations to a supplied
behavior object. This is the single extension boundary:

- A stateless behavior type implements `StateValueBehaviorProtocol`:
  `copy_state`, `validate_state`, `replace_state`, `update_state`,
  `states_equal`, `state_repr`, `hash_state`, and the illustrative
  `dummy_method` hook.
- A behavior instance is passed explicitly to each wrapper at construction,
  keeping the dependency visible and allowing configured or test-specific
  implementations. Concrete owned objects must not be required to inherit
  from the wrapper templates.
- Replacement operations preserve the behavior instance of the original
  value object.
- For concrete owned objects, validation is owned by the object itself
  through `validate_state()`; a behavior implementation's `validate_state()`
  delegates to that method so the wrapper never duplicates invariant checks.
- Replacement and update payloads are typed as `Any`; the owned state object
  understands its own change representation and invariants through
  `replace()` and `update()`. The shared behavior delegates those operations
  rather than interpreting a universal shape.
- The original mapping-based examples remain supported as a compatibility
  fallback (behavior retains a mapping field-name path); new owned-object
  types should implement `validate_state()` directly.
- `dummy_method` is an example extension point for users adapting the
  template; it is not a required domain behavior.
- There is no global dispatch registry and no default behavior in `src`;
  each caller supplies its own `StateValueBehaviorProtocol` implementation.

### `ValueObjectInterface`

An abstract base with `__slots__ = ()` that defines the required value
semantics only: `state_implementations`, `replace(changes)`,
`dummy_method()`, `__eq__`, `__repr__`. It stores no instance data; concrete
implementations own their own private state.

### Wrapper templates

- `StateValueObjectImmutable` — copies state at construction via the
  behavior, validates it, returns defensive copies from its properties, and
  produces new instances from `replace()`. Hashing is available only through
  the behavior's `hash_state` policy.
- `StateValueObjectMutable` — the controlled-mutation counterpart: public
  `update()` validates the complete resulting state; equality remains
  state-based; internal mutable state is never exposed directly.

### Validation helpers

`validate_state(state, *, validators=())` accepts arbitrary state and runs
whole-state validator callables, normalizing `ValueError` into
`ValueValidationError`. All state-specific validation belongs to the owned
object or the supplied behavior, never to this helper.

## Test Plan

Covered by `tests/design_patterns_templates/value_semantics/`:

1. Equal state compares equal even when instances are distinct.
2. Different state compares unequal.
3. Immutable values reject unsupported mutation.
4. Replacement creates a new value and leaves the original unchanged.
5. Copies do not unexpectedly share mutable nested state.
6. Invalid construction input raises a clear validation error.
7. Public updates on mutable values preserve invariants.
8. Hashing is available only for values that satisfy the hashability policy.
9. Representations contain the relevant value state and remain useful for
   debugging.
10. Templates remain independent of application-specific modules.

Tests verify observable value behavior rather than implementation details
such as whether `dataclasses` or a custom class is used. Mapping to files:
items 1–9 primarily in `test_value_object.py` and
`test_value_object_behaviors.py`; validation semantics in
`test_validation.py`; domain independence holds by construction (the package
imports nothing outside the standard library).

## Non-Goals

- Do not build a universal object framework.
- Do not force every project class to inherit from a value base class.
- Do not hide resource ownership or I/O behind value objects.
- Do not add serialization, persistence, or validation policy that belongs
  to a concrete domain.
- Do not treat value semantics as a replacement for identity-based entities
  or resource-owning services.

## Acceptance Criteria

- The package structure is documented and domain-neutral.
- At least one small value-oriented template has a clear, tested contract.
- Equality, copying, mutation, validation, and hashing behavior are explicit.
- The templates have no dependencies on concrete analysis backends.
- A domain implementation can use the templates through composition without
  inheriting unrelated behavior.
- Additional templates require demonstrated reuse and documented semantics
  before being added.

## Migration Log (Completed Work)

### Phases 1–4: contract, scaffold, implementation, contract tests — completed

- Contract clarified: immutable and mutable wrappers, explicit
  copy/replacement/equality/hashing/validation semantics; rules for nested
  mutable values recorded in the design rules above.
- Package scaffold created under
  `src/lammps_trajectory_analysis_tools/design_patterns_templates/value_semantics/`.
- Templates, protocols, interface, behaviors, and validation implemented per
  the contract above.
- Contract tests added under
  `tests/design_patterns_templates/value_semantics/` and passing.

### Phase 5: expansion evaluation — completed

- `NumericStateImplementation` added as a second owned-object example,
  demonstrating that the package boundary is reusable without per-type
  helper modules or inheritance.
- The former shared default behavior `StateValueBehavior` was removed from
  `src` because no production code constructed it; each caller now supplies
  its own `StateValueBehaviorProtocol` implementation directly.
- Expansion policy confirmed: add another template only when a repeated use
  case demonstrates that it belongs in the shared package.

### Evolution from the original proposal

The original plan proposed a five-module package (`value_object.py`,
`value_object_builder.py`, `validation.py`, `protocols.py`). As built, the
package has nine modules: the builder module was dropped in favor of the
separate builder feature, the value object split into an interface plus
immutable and mutable wrappers, behavior delegation was extracted into
`protocols.py`/`value_object_behaviors.py`, and two concrete example
implementations were added. The original text is preserved in
[docs/design_patterns_templates_plan.md](../../../../docs/design_patterns_templates_plan.md)
history; see `context.md` for the decision log.

### Historical note

This plan was converted into an ICM feature workspace on 2026-10-04. The
original document at `docs/design_patterns_templates_plan.md` is now a
pointer to this file and the parent collection plan.
