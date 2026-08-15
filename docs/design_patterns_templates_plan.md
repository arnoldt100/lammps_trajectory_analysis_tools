# Design Patterns Templates Plan

## Objective

Create a reusable home for design-pattern templates that provide starting points for new implementations without coupling them to a specific analysis domain.

The first pattern collection will be `value_semantics`, based on value-oriented design principles:

- objects are defined by their state rather than identity;
- equal state produces equal values;
- copies are independent unless sharing is explicit and documented;
- invariants are established at construction or controlled update boundaries;
- operations are predictable, composable, and easy to test.

## Proposed Structure

```text
src/
  lammps_trajectory_analysis_tools/
    design_patterns_templates/
      __init__.py
      value_semantics/
        __init__.py
        value_object.py
        value_object_builder.py
        validation.py
        protocols.py

docs/
  design_patterns_templates_plan.md

tests/
  design_patterns_templates/
    value_semantics/
      test_value_object.py
      test_validation.py
```

The exact module split may be reduced if a smaller initial template is sufficient. The public package should expose only stable, intentionally reusable templates.

## Design Rules

- Keep templates domain-neutral. They must not import trajectory, analysis, writer, HDF5, or MDAnalysis modules.
- Prefer composition and small protocols over inheritance-heavy frameworks.
- Make value state explicit and inspectable.
- Define equality from value state, not object identity.
- Ensure hashing is available only when the value is immutable and all participating fields are hashable.
- Make copying behavior explicit, especially for mutable nested values.
- Validate invariants at construction and at every public mutation boundary.
- Avoid hidden global state, registries, singletons, and backend resources in value templates.
- Keep algorithms that operate on values separate from the value object where that improves reuse.
- Use type annotations and precise docstrings for the intended extension points.
- Keep the templates small enough that a domain implementation can understand and adapt them rather than inherit accidental policy.

## Initial Template Candidates

### Immutable value object

A frozen, value-oriented template for objects whose state should not change after construction.

Expected behavior:

- construction validates required invariants;
- equality compares all declared value fields;
- representation includes useful state for debugging;
- hashing is available only when safe;
- replacement produces a new value rather than mutating the existing object.

Possible Python starting points include `dataclasses` with `frozen=True` or a small protocol describing equality, copying, and serialization expectations.

### Mutable value object

A controlled-mutation template for values that must change during a workflow.

Expected behavior:

- public updates validate the complete resulting state;
- equality remains state-based;
- copying produces an independent value unless shallow sharing is explicitly documented;
- mutation methods do not expose internal mutable state accidentally.

This template should be added only if an immutable template cannot cover the initial use cases.

### Value validation helpers

Small helpers or protocols for validating invariants without imposing domain-specific rules.

Examples of reusable concerns:

- required fields;
- valid ranges;
- compatible shapes or dimensions;
- normalized names or identifiers;
- validation of nested value objects.

Validation helpers should return clear errors and avoid silently coercing invalid input.

### Value-object protocol

A lightweight protocol describing the behavior expected from value-oriented domain types. It should not require a large inheritance hierarchy.

Potential capabilities:

- state-based equality;
- explicit copy or replacement operation;
- stable representation;
- optional serialization to plain data;
- optional validation hook.

Only capabilities needed by actual templates should be included in the first version.

## API and Naming Principles

- Use names that describe behavior rather than the eventual domain.
- Prefer `ValueObject`, `ImmutableValue`, or similarly direct names over pattern-jargon-heavy names.
- Avoid a generic base class when a dataclass, protocol, or helper function is clearer.
- Keep constructors unsurprising and avoid accepting arbitrary `*args` and `**kwargs` in public templates.
- Document whether nested values are copied deeply, copied shallowly, or required to be immutable.
- Document whether serialization is part of the template or left to domain-specific code.

## Test Plan

Add focused tests for the template contract:

1. Equal state compares equal even when instances are distinct.
2. Different state compares unequal.
3. Immutable values reject unsupported mutation.
4. Replacement creates a new value and leaves the original unchanged.
5. Copies do not unexpectedly share mutable nested state.
6. Invalid construction input raises a clear validation error.
7. Public updates on mutable values preserve invariants.
8. Hashing is available only for values that satisfy the hashability policy.
9. Representations contain the relevant value state and remain useful for debugging.
10. Templates remain independent of application-specific modules.

Tests should verify observable value behavior rather than implementation details such as whether `dataclasses` or a custom class is used.

## Implementation Phases

### Phase 1: Clarify the common contract

- Decide whether the first release contains only immutable values.
- Define copy, replacement, equality, hashing, and validation semantics.
- Decide the supported Python version and standard-library features.
- Record rules for nested mutable values.

### Phase 2: Create the package scaffold

- Create `design_patterns_templates/` under the main package.
- Create the `value_semantics/` subpackage.
- Add minimal `__init__.py` files.
- Export only the first stable template and its supporting types.

### Phase 3: Implement the initial templates

- Implement the smallest useful immutable value template.
- Add validation and protocol support only where they reduce repeated domain code.
- Keep domain-specific examples outside the reusable package or in documentation examples.

### Phase 4: Add contract tests

- Add the value-semantics tests described above.
- Run them independently from analysis, trajectory, and writer tests.
- Add examples showing how a domain type can use the template through composition.

### Phase 5: Evaluate expansion

- Review actual consumers before adding mutable-value or serialization templates.
- Add another template only when a repeated use case demonstrates that it belongs in the shared package.
- Document limitations and intentional non-goals.

## Non-Goals

- Do not build a universal object framework.
- Do not force every project class to inherit from a value base class.
- Do not hide resource ownership or I/O behind value objects.
- Do not add serialization, persistence, or validation policy that belongs to a concrete domain.
- Do not treat value semantics as a replacement for identity-based entities or resource-owning services.

## Acceptance Criteria

- The proposed package structure is documented and domain-neutral.
- At least one small value-oriented template has a clear, tested contract.
- Equality, copying, mutation, validation, and hashing behavior are explicit.
- The templates have no dependencies on concrete analysis backends.
- A domain implementation can use the templates through composition without inheriting unrelated behavior.
- Additional templates require demonstrated reuse and documented semantics before being added.
