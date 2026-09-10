# Q&A: Supporting Multiple Concrete Data Writers via `data_writer_factory`

**Question:** If there were more than one concrete data writer other than
`HDF5LopSfFccTrajectoryDataWriter`, with a different layout and metadata
format, how would `data_writer_factory` be used or modified to build the
corresponding objects?

## What `data_writer_factory` actually is

It's a single `BuilderRegistry[Any]` instance — a plain `dict[str, builder]`
under the hood, with `register_builder(key, builder)` and
`build(key, *args, **kwargs)`. It has no notion of "HDF5" or "LOP SF FCC"
baked in; it's domain-neutral. All the HDF5/LOP-specific behavior comes
purely from *what gets registered under which keys* in
[`data_writer_utils/__init__.py`](../src/lammps_trajectory_analysis_tools/data_writer_utils/__init__.py).

Currently four keys are registered for the one concrete writer:

- `LopSfFccRunMetadataBuilderKey` → builds the metadata value object
- `LopSfFccTrajectoryLayoutBuilderKey` → builds the layout value object
- `HDF5LopSfFccTrajectoryDataWriterBuilderKey` → builds the concrete
  `HDF5LopSfFccTrajectoryDataWriter`
- `HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey` → a *composite*
  builder that receives the registry itself (dependency-injected) and
  composes metadata + layout into a `HDF5LopSfFccTrajectoryWriterValueObject`

See [`builder_registry.py`](../src/lammps_trajectory_analysis_tools/design_patterns_templates/builder/builder_registry.py)
for the registry implementation.

## Adding a second concrete writer (different layout + metadata format)

No changes to `BuilderRegistry` are needed — it's already generic. You'd:

1. **Define new state/value types** analogous to `LopSfFccRunMetadata` /
   `LopSfFccTrajectoryLayout` / `HDF5LopSfFccTrajectoryWriterValueObject`,
   but shaped for the new format (e.g. `NewFormatRunMetadata`,
   `NewFormatTrajectoryLayout`, `NewFormatTrajectoryWriterValueObject`).

2. **Define new builder key constants**, e.g. in a module parallel to
   `lop_sf_fcc_trajectory_writer_builder_keys.py`:
   - `NewFormatRunMetadataBuilderKey`
   - `NewFormatTrajectoryLayoutBuilderKey`
   - `NewFormatTrajectoryDataWriterBuilderKey`
   - `NewFormatTrajectoryWriterValueObjectBuilderKey`

   These just need to be distinct strings so they don't collide with the
   existing keys in the same registry.

3. **Define new builder classes** (`NewFormatRunMetadataBuilder`,
   `NewFormatTrajectoryLayoutBuilder`, `NewFormatTrajectoryDataWriterBuilder`),
   following the same trivial `__call__(*args, **kwargs) -> Product` pattern.

4. **Define a new composite value-object builder**
   (`NewFormatTrajectoryWriterValueObjectBuilder`), constructed the same
   way — taking the registry in its `__init__` so it can call back into
   `registry.build(NewFormatRunMetadataBuilderKey, ...)` and
   `registry.build(NewFormatTrajectoryLayoutBuilderKey, ...)` to assemble
   its product, mirroring `HDF5LopSfFccTrajectoryWriterValueObjectBuilder`.

5. **Register all of these on the same `data_writer_factory` instance** in
   `data_writer_utils/__init__.py`, right after the existing four
   `register_builder` calls:

   ```python
   data_writer_factory.register_builder(NewFormatRunMetadataBuilderKey, NewFormatRunMetadataBuilder())
   data_writer_factory.register_builder(NewFormatTrajectoryLayoutBuilderKey, NewFormatTrajectoryLayoutBuilder())
   data_writer_factory.register_builder(NewFormatTrajectoryDataWriterBuilderKey, NewFormatTrajectoryDataWriterBuilder())
   data_writer_factory.register_builder(
       NewFormatTrajectoryWriterValueObjectBuilderKey,
       NewFormatTrajectoryWriterValueObjectBuilder(data_writer_factory),
   )
   ```

   Since `register_builder` raises `BuilderRegistrationError` on duplicate
   keys, all eight keys just need to be unique strings.

6. **Export the new keys/builders/types** in `__all__` alongside the
   existing ones.

## How a caller picks the right writer

Callers already select behavior purely by which key they pass to
`data_writer_factory.build(key, ...)` — there's no branching logic inside
the factory itself. So with two formats registered, calling code (e.g. a
CLI or config-driven dispatcher) would map a user-facing choice (like a
`--format hdf5|newformat` flag or a config field) to the corresponding
`*ValueObjectBuilderKey`, then call
`data_writer_factory.build(that_key, file_path, metadata, layout)`.

If you wanted a more ergonomic single entry point (e.g.
`data_writer_factory.build_writer(format="hdf5", ...)`), that would require
adding a thin dispatch helper on top of `BuilderRegistry`, but the
registry/factory itself stays unchanged — that's a decision point, not
something forced by the current design.

## Example: instantiating the existing HDF5 writer today

Callers never build `HDF5LopSfFccTrajectoryDataWriter` directly. Instead,
they build the composite writer value object (via
`HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey`) and use it as a context
manager; the value object builds and owns the concrete writer internally
through `LopSfFccTrajectoryWriterBehavior.build_writer`, which in turn calls
`data_writer_factory.build(HDF5LopSfFccTrajectoryDataWriterBuilderKey, ...)`.

```python
from pathlib import Path
from datetime import datetime, timezone

from lammps_trajectory_analysis_tools.data_writer_utils import (
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    data_writer_factory,
)

metadata_arguments = {
    "time_units": 0.002,
    "time_units_label": "ps",
    "number_of_trajectories": 2,
    "generation_date": datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
    "compiler_build_flags": ("-O3", "-march=native"),
    "generating_machine": "nimzoindian",
    "lmod_modules": ("gcc/13.2.0", "openmpi/4.1.6"),
}
layout_arguments = {"number_of_atoms": 6, "length_units_label": "angstrom"}

# Build the composite value object; no writer is opened yet.
value_object = data_writer_factory.build(
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    file_path=Path("trajectory.h5"),
    metadata=metadata_arguments,
    layout=layout_arguments,
)

# Entering the context creates the concrete HDF5LopSfFccTrajectoryDataWriter
# and yields it as `writer`; exiting closes it.
with value_object as writer:
    writer.append_trajectory_frames(
        0,               # trajectory_index
        step_number,     # np.ndarray
        positions,       # np.ndarray
        lop_sf_fcc,      # np.ndarray
        box_lengths,     # np.ndarray
        box_angles,      # np.ndarray
    )
```

For a new writer format, the equivalent call would simply target the new
format's own `*ValueObjectBuilderKey`:

```python
value_object = data_writer_factory.build(
    NewFormatTrajectoryWriterValueObjectBuilderKey,
    file_path=Path("trajectory.newformat"),
    metadata=new_format_metadata_arguments,
    layout=new_format_layout_arguments,
)
with value_object as writer:
    ...
```
