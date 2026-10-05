# Context - LOP SF FCC HDF5 Writer

Status snapshot for the HDF5 writer feature. Per the ICM rules, this file
must be updated whenever the feature's behavior, data flow, or boundaries
change.

Last reviewed: 2026-10-05.

## Implementation Status

### Done

- Full writer stack in
  `src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc/hdf5_writer/`:
  `LopSfFccRunMetadata`, `LopSfFccTrajectoryLayout`,
  `LopSfFccTrajectoryWriterState`, `LopSfFccTrajectoryWriterBehavior`,
  `HDF5LopSfFccTrajectoryWriterValueObject` behind
  `LopSfFccTrajectoryWriterValueObjectInterface`, four builder keys and
  builders, and the concrete `HDF5LopSfFccTrajectoryDataWriter`.
- Registry: `lop_sf_fcc_data_writer_factory` owned and populated (four
  builders) by `hdf5_writer/__init__.py` — the single registration site;
  re-exported from `lib/lop_sf_fcc/__init__.py`.
- Append mode: `open_for_append()` on both the concrete writer and the value
  object, supporting chunked multi-`run()` workflows; step ordering is
  enforced across the stored tail.
- Consumers wired: the orchestrator builds the value object
  (`_set_data_writer_attributes`); the backend's `LOP_SF_FCC._conclude`
  creates on the first `run()` and appends on later runs; one HDF5
  trajectory group per analysed frame, numbered across runs.
- Full-run verification inherited from the orchestrator/backend features
  (2026-10-04): all 5001 argon frames, 10 workers, 547 MB output, 5001
  complete trajectory groups with ordered step numbers.
- Feature workspace created 2026-10-05 together with the module relocation
  from `data_writer_utils/`; suite green before and after (330 passed,
  2 skipped).

### Pending

- None blocking. Deferred design questions (tracked in the plan): whether
  very large runs should split into one file per trajectory joined by HDF5
  external links; whether MPI-backed parallel writing is ever required.

### Not planned

- Implementing the generic `DataWriterProtocol` (single-stream surface does
  not fit trajectory-indexed five-array writes).
- An overwrite mode (`create()` refuses existing targets by design).
- Owning the generic writer machinery (`data_writer_utils/` protocol,
  exceptions, `HDF5DataWriter`) — that package stays global under the
  project-wide plan.

## Decision Log

- **Handle excluded from value identity:** the open HDF5 handle is a
  resource, not a value; equality, `repr`, and `copy_state` never touch it.
- **`update()` blocked while open** because `create()` fixes on-disk shapes
  and attributes from the in-memory state; `replace()` yields a handle-free
  object instead.
- **No overwrite (h5py mode `"x"`)** aligns with the shared Data Writer
  Contract Plan and intentionally diverges from `HDF5DataWriter`.
- **Pre-created `traj_NNNNN` groups** make the file self-describing and turn
  a missing group into a genuine error.
- **Per-feature registry:** the writer owns `lop_sf_fcc_data_writer_factory`;
  registries are not shared across writers (registration-order coupling is
  hidden global state). This supersedes the shared-`data_writer_factory`
  guidance in the old Q&A document.
- **Modules keep their `lop_sf_fcc_` prefixes** after the move to minimize
  diff; only the registry was renamed.

## Current Data Flow

```text
LopSfFcc._set_data_writer_attributes (orchestrator feature)
  │ lop_sf_fcc_data_writer_factory.build(
  │     HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
  │     file_path, metadata=args, layout=args)
  ▼
HDF5LopSfFccTrajectoryWriterValueObject   (no handle yet)
  │ passed to LOP_SF_FCC(data_writer=...)
  ▼
LOP_SF_FCC._conclude (backend feature, main process only)
  │ first run:  with value_object as writer:          → create()
  │ later runs: with value_object.open_for_append() as writer:
  ▼
writer.append_trajectory_frames(index, step_numbers, positions,
                                lop_sf_fcc, box_lengths, box_angles)
  │ validate all five arrays → resize tail → assign (all-or-nothing)
  ▼
HDF5LopSfFccTrajectoryDataWriter (sole h5py user; built via registry)
```

## Maintenance Rule

Any change to the writer contract (file layout, validation rules, lifecycle,
error categories, builder wiring, or registry ownership) requires, in the
same change:

1. Updated focused tests under `tests/lib/lop_sf_fcc/hdf5_writer/`.
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every cross-feature consumer listed in `README.md`
   (orchestrator, mdanalysis backend) and the generic boundary in
   `data_writer_utils`.
