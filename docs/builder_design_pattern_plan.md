# Builder Design Pattern Plan

## Objective

Create a reusable, domain-neutral builder/registry template under
`design_patterns_templates/`, generalizing the registry-based builder pattern
already used by `lop_sf_fcc_builder.py` and `lammps_analysis_tool_builder.py`.

The pattern being generalized:

- A *product* is the object actually being constructed (e.g. `LopSfFcc`).
- A *concrete builder* is a callable that constructs a product directly:
  `builder(*args, **kwargs) -> Product`.
- A *builder key* uniquely identifies a concrete builder.
- A *registry* maps keys to concrete builders and exposes `register_builder`
  and `build`.

## Proposed Structure

```text
src/
  lammps_trajectory_analysis_tools/
    design_patterns_templates/
      builder/
        __init__.py
        builder_protocol.py
        builder_registry.py
        exceptions.py

docs/
  builder_design_pattern_plan.md

tests/
  design_patterns_templates/
    builder/
      test_builder_registry.py
      test_builder_protocol.py
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
  responsible for instantiating and populating its own registry (as
  `lammps_analysis_tool_builder.py` does today).
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
move into the shared template.

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

## Implementation Phases

### Phase 1: Confirm the contract

- Confirm concrete builders are single-step callables (`builder(*args,
  **kwargs) -> Product`), not zero-arg-instantiate-then-call.
- Confirm duplicate registration is an error, not a silent overwrite.

### Phase 2: Create the package scaffold

- Create `design_patterns_templates/builder/`.
- Add minimal `__init__.py` exporting `BuilderRegistry`, `SupportsBuild`,
  `BuilderKeyError`, and `BuilderRegistrationError`.

### Phase 3: Implement the template

- Implement `builder_protocol.py`, `exceptions.py`, and `builder_registry.py`.

### Phase 4: Add contract tests

- Add the tests described above under
  `tests/design_patterns_templates/builder/`.

### Phase 5: Migrate `lammps_analysis_tool_builder.py` (optional follow-up)

- Only after the template is reviewed and tested, consider updating
  `lammps_analysis_tool_builder.py` to use `BuilderRegistry` instead of its
  local `GeneralLammpsAnalysisToolFactory`.

## Non-Goals

- Do not require concrete builders to implement a base class or zero-arg
  constructor.
- Do not add product-specific validation or construction logic to the
  template.
- Do not silently overwrite existing registrations.
- Do not migrate existing domain builders as part of this plan; migration is
  a follow-up once the template is accepted.

## Acceptance Criteria

- The package structure is documented and domain-neutral.
- `BuilderRegistry` raises `BuilderRegistrationError` on duplicate
  registration and `BuilderKeyError` on unknown keys.
- Concrete builders are called directly with arbitrary `*args, **kwargs`.
- Tests cover registration, duplicate registration, unknown-key lookup, and
  registry independence.
