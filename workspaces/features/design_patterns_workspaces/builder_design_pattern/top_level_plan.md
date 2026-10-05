# Top Level Plan - Builder Design Pattern

This is the canonical standing plan for the builder design pattern feature.
It inherits all project-wide rules from
[../../../../workspaces/top_level_plan.md](../../../../workspaces/top_level_plan.md)
and adds feature-specific rules; it must not weaken the project-wide rules.

## Objective

Maintain a reusable, domain-neutral builder/registry template under
`design_patterns_templates/builder/`, generalizing the registry-based builder
pattern already used by `lop_sf_fcc_builder.py` and other domain builders.

The pattern being generalized:

- A *product* is the object actually being constructed (e.g. `LopSfFcc`).
- A *concrete builder* is a callable that constructs a product directly:
  `builder(*args, **kwargs) -> Product`.
- A *builder key* uniquely identifies a concrete builder.
- A *registry* maps keys to concrete builders and exposes `register_builder`
  and `build`.

## Package Structure

```text
src/
  lammps_trajectory_analysis_tools/
    design_patterns_templates/
      builder/
        __init__.py
        builder_protocol.py
        builder_registry.py
        exceptions.py

tests/
  design_patterns_templates/
    builder/
      test_builder_registry.py
      test_builder_protocol.py
```

Feature workspace (plan, boundaries, and status only — no code):

```text
workspaces/features/design_patterns_workspaces/builder_design_pattern/
  README.md
  context.md
  top_level_plan.md
```

## Design Rules

- Keep the template domain-neutral. It must not import trajectory, analysis,
  writer, HDF5, or MDAnalysis modules.
- Keep every class-level and instance-level data attribute private with a
  single leading underscore; expose required external access through
  properties or methods.
- A concrete builder is called directly with arbitrary positional and keyword
  arguments to produce a product: `builder(*args, **kwargs) -> Product`. It
  does **not** require zero-arg instantiation followed by a separate call.
- Registry instances hold no hidden global state; a domain module is
  responsible for instantiating and populating its own registry.
- Every domain builder migration must include registry integration. This is a
  required step even when only one concrete builder currently exists;
  deferring registry integration until a second implementation appears is not
  supported.
- Registering a key that is already registered raises
  `BuilderRegistrationError`. Silent overwrite is not supported by default.
- Building with an unregistered key raises `BuilderKeyError`.

## Builder Contract

### `builder_protocol.py`

- `SupportsBuild` — a `Protocol` describing a concrete builder:
  `__call__(self, *args: Any, **kwargs: Any) -> P`.

### `exceptions.py`

- `BuilderKeyError(KeyError)` — raised when `build()` is called with an
  unregistered key.
- `BuilderRegistrationError(ValueError)` — raised when `register_builder()` is
  called with a key that is already registered.

### `builder_registry.py`

- `BuilderRegistry[P]`
  - `register_builder(key: str, builder: SupportsBuild[P]) -> None` — raises
    `BuilderRegistrationError` if `key` is already registered.
  - `build(key: str, *args: Any, **kwargs: Any) -> P` — raises
    `BuilderKeyError` if `key` is not registered; otherwise forwards
    `*args, **kwargs` to the registered builder and returns its result.
  - `has_builder(key: str) -> bool`
  - `keys() -> frozenset[str]`

## Migration Sketch (domain code, not part of the template)

```python
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import BuilderRegistry

analysis_tool_factory: BuilderRegistry[Any] = BuilderRegistry()
analysis_tool_factory.register_builder(key_lop_sf_fcc_factory, LopSfFccFactory())
```

`LopSfFccFactory` itself remains domain code; only the registry and protocol
live in the shared template.

## Test Plan

1. Registering a builder and calling `build()` returns the expected product,
   with positional and keyword arguments forwarded unchanged.
2. Calling `build()` with an unregistered key raises `BuilderKeyError`.
3. Calling `register_builder()` twice with the same key raises
   `BuilderRegistrationError`, and the original registration is preserved.
4. `has_builder()` and `keys()` accurately reflect registration state.
5. Two `BuilderRegistry` instances do not share state.
6. The template package has no dependency on trajectory, analysis, writer,
   HDF5, or MDAnalysis modules.
7. Domain concrete builders (e.g. `LoopTimerBuilder`) satisfy `SupportsBuild`
   and forward constructor arguments unchanged.
8. Each consuming domain package exposes one factory instance with one
   registration site.
9. Domain factories build their product and raise template exceptions for
   unknown keys and duplicate registrations.

## Non-Goals

- Do not require concrete builders to implement a base class or zero-arg
  constructor.
- Do not add product-specific validation or construction logic to the
  template.
- Do not silently overwrite existing registrations.
- Do not migrate existing domain builders as part of this template feature;
  each migration is planned and executed in the owning domain feature.

## Acceptance Criteria

- The package structure is documented and domain-neutral.
- `BuilderRegistry` raises `BuilderRegistrationError` on duplicate
  registration and `BuilderKeyError` on unknown keys.
- Concrete builders are called directly with arbitrary `*args, **kwargs`.
- Tests cover registration, duplicate registration, unknown-key lookup, and
  registry independence.

## Migration Log (Completed Work)

### Template creation (Phases 1–4 of the original plan) — completed

- Contract confirmed: concrete builders are single-step callables; duplicate
  registration is an error, not a silent overwrite.
- Package scaffold created under
  `src/lammps_trajectory_analysis_tools/design_patterns_templates/builder/`
  with a minimal `__init__.py` exporting `BuilderRegistry`, `SupportsBuild`,
  `BuilderKeyError`, and `BuilderRegistrationError`.
- `builder_protocol.py`, `exceptions.py`, and `builder_registry.py`
  implemented per the contract above.
- Contract tests added under `tests/design_patterns_templates/builder/`.

### Timer module migration — completed

The timer modules adopted the shared builder contract:

- `LoopTimer` kept as the product; constructor, properties, lifecycle,
  context-manager behavior, output, and exceptions unchanged; it does not
  inherit from a builder type.
- `LoopTimerBuilder` is a direct callable builder forwarding
  `*args, **kwargs` to `LoopTimer`; `LoopTimerBuilderKey` is unchanged.
- `GeneralTimerBuilder`'s local registry was replaced by `BuilderRegistry`;
  the name remains as a compatibility alias for `BuilderRegistry`.
- The duplicate module-level registration was corrected: the single public
  `timer_object_factory` is defined in `timer_utils/__init__.py`, which
  registers `LoopTimerBuilder()` exactly once; `GeneralTimerBuilder.py` no
  longer creates or populates a factory.
- Callers use `build(key, *args, **kwargs)`; registry integration is covered
  by the timer and builder test suites.

### Historical note

This plan was converted into an ICM feature workspace on 2026-10-04. The
original document at `docs/builder_design_pattern_plan.md` is now a pointer
to this file.
