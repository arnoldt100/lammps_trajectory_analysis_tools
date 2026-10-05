# Context - Value Semantics

Status snapshot and decision log for the value-semantics template feature.
Per the ICM rules, this file must be updated whenever the feature's behavior,
data flow, or boundaries change.

Last reviewed: 2026-10-04.

## Implementation Status

### Done

- Template package implemented (nine modules) and exported:
  `src/lammps_trajectory_analysis_tools/design_patterns_templates/value_semantics/`,
  re-exported selectively from `design_patterns_templates/__init__.py`.
- Contract tests in place and passing:
  `tests/design_patterns_templates/value_semantics/test_value_object.py`,
  `test_value_object_behaviors.py`, `test_validation.py`, covering the full
  test plan in `top_level_plan.md`.
- Two concrete owned-state examples shipped: `ConcreteStateImplementation`
  (message state) and `NumericStateImplementation` (integer state), proving
  reuse without per-type helper modules or wrapper inheritance.
- Domain consumers active: accumulator value objects
  (`array_accumulator_value.py`, `array_accumulator.py`) and the HDF5
  trajectory-writer value object interface
  (`lib/lop_sf_fcc/hdf5_writer/lop_sf_fcc_trajectory_writer_value_object_interface.py`,
  owned by the `lop_sf_fcc_hdf5_writer_workspaces` feature).
- Usage guide published at
  `docs/value_semantics_package_usage_guide.md` (copy-and-adapt tutorial).
- Feature workspace converted to ICM on 2026-10-04; the former canonical
  document `docs/design_patterns_templates_plan.md` is now a pointer here
  and to the parent collection plan.

### Pending

- No open template work. Any new template (e.g. serialization support) must
  satisfy the expansion policy: demonstrated reuse plus documented semantics
  before addition.

### Not planned

- A default/shared behavior implementation in `src` (removed; callers supply
  their own `StateValueBehaviorProtocol`).
- Global dispatch registries, universal object frameworks, or mandated
  inheritance from the wrapper templates.

## Decision Log

### Helper-module structure (from the original plan's Q&A)

Question: should each `ConcreteStateImplementation` class have its own helper
file, or one common helper file?

Decided: hybrid structure. Genuinely shared, type-independent functions live
in one common module (`concrete_state_implementation_helpers.py`, analogous
to `value_object_behaviors.py`); each substantially different owned state
type may get its own helper module when its functions encode type-specific
rules. Helper functions accept explicit state and arguments rather than
depending heavily on one concrete class, keeping testing simple and avoiding
circular imports. Class spelling standardized as
`ConcreteStateImplementation` (capital I); filenames stay snake_case.

### Package-wide behavior decision (finalized)

When behavior is identical for every owned object in a package, use one
stateless package behavior type and pass a behavior instance explicitly to
each wrapper. This keeps the dependency visible at construction while
allowing configured or test-specific implementations. Concrete owned objects
must satisfy the package's behavior contract but do not inherit from the
templates.

`StateValueBehavior` was the default shared behavior; it was removed from
`src` because no production code constructed it, and each caller now
supplies its own `StateValueBehaviorProtocol` implementation directly.
Replacement operations preserve the behavior instance of the original value
object.

### Phase 5 evaluation outcome

The removed default behavior was reusable for operations with universal
meaning for arbitrary state: copying, validation dispatch, equality,
representation, hashing, and `dummy_method` delegation. Replacement and
update cannot be defined safely for every `Any` state, so the behavior
delegates those operations to the owned object's own `replace()`/`update()`
understanding of its change representation; the original mapping examples
remain supported as a compatibility fallback. Validation is owned by the
concrete object through `validate_state()`; the behavior's
`validate_state()` delegates to it, so the wrapper never duplicates
invariant checks. This is the intended extension boundary — not a reason to
add type checks or a global dispatch registry.

## Current Data Flow

```text
domain code defines an owned state type (with validate_state/replace/update)
        │
domain code implements StateValueBehaviorProtocol (stateless)
        │
wrapper constructed: StateValueObject*(state, behavior)
  → behavior.copy_state(state)      (defensive copy in)
  → behavior.validate_state(copied) (delegates to owned object)
        │
property access returns behavior.copy_state(internal)  (defensive copy out)
        │
replace(changes)  → behavior.replace_state(...) → NEW wrapper, same behavior
update(changes)   → behavior.update_state(...)  → validated mutation (mutable)
equality/repr/hash→ behavior.states_equal / state_repr / hash_state
```

No hidden global state: every wrapper holds only its own `_state` and
`_behavior` (private, single underscore, `__slots__`).

## Maintenance Rule

Any change to the public contract (protocols, interface, wrappers, behaviors,
validation, or package layout) requires, in the same change:

1. Updated contract tests under
   `tests/design_patterns_templates/value_semantics/`.
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every consumer listed in `README.md` (currently accumulator
   and data_writer_utils).
