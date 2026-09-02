# Data Writer Contract Plan

## Objective

Define a backend-neutral contract for writers that persist analysis data to an output target. Concrete writers may use HDF5, text, databases, or another storage format, but callers should depend on the same data and life cycle semantics.

## Scope

This contract covers writers that support both:

- writing one complete dataset in a single operation;
- appending one or more frames to an existing frame sequence.

It does not prescribe a file format, serialization library, storage layout, or file extension.

## Core Concepts

- **Output target**: The destination identified when the writer is constructed.
- **Data stream**: The named logical collection written by the writer. A backend may represent this as a dataset, table, file section, or another structure.
- **Frame**: One item in an ordered sequence of data. Frames may be scalar, vector, matrix, or higher-dimensional values, but every frame in one stream must have the same shape and compatible type.
- **Frame axis**: The leading logical dimension used when multiple frames are stored as one sequence.

## Proposed Interface

A concrete writer should provide operations equivalent to:

```text
Writer(output_target, stream_name, frame_shape, data_type)
create()
write_data(data)
append_data(frames)
close()
``
```

The concrete API may use backend-specific names or configuration, but adapters should preserve these semantics.

## Proposed Module Layout

Keep the shared contract small and keep backend details in concrete modules:

- `data_writer_utils/data_writer_protocol.py`: `DataWriterProtocol`, including configuration, complete writes, frame appends, and lifecycle operations.
- `data_writer_utils/exceptions.py`: predictable contract-level configuration, lifecycle, and target errors.
- `data_writer_utils/hdf5_data_writer.py`: the HDF5 adapter and its `h5py` operations.
- `tests/test_hdf5_data_writer.py`: contract behavior tests against the HDF5 adapter; backend-specific tests should remain separate if needed.

The initial HDF5 policy is that `create()` replaces an existing target, `write_data()` replaces the stream contents, and `data_type` is a safe-cast boundary. The configured `frame_shape` is stored after a leading, resizable frame axis. `append_data()` accepts either one frame or a batch and validates the entire input before changing the dataset.

### Construction

Construction records the output target and stream configuration. It should not require the target to be created or opened unless the backend requires eager validation.

The configuration should identify:

- the output target;
- the logical stream name;
- the shape of one frame, or an explicitly documented complete-data shape;
- the data type or type policy.

The contract must document which shape convention is used. The preferred convention is `frame_shape`, with the number of frames managed separately by the writer.

### `create()`

`create()` prepares a new output target and initializes the named data stream.

Required behavior:

- create the destination if it does not exist;
- initialize an empty stream that can accept frames when appending is supported;
- establish the configured type and frame shape;
- reject invalid configuration or an unusable target with a documented exception.

The overwrite behavior for an existing target must be explicit. A writer must either replace it, refuse to replace it, or provide a separate append/open mode.

### `write_data(data)`

`write_data` writes the complete dataset in one operation.

Required behavior:

- accept data whose shape and type satisfy the configured contract;
- replace the stream's current contents, or reject the operation if replacement is not supported; this policy must be documented;
- preserve the complete input data and its ordering;
- avoid silently truncating, reshaping, or dropping values;
- reject incompatible shape, rank, or type with a documented exception.

`write_data` is not an append operation. Calling it with a second complete dataset must not be interpreted as adding frames unless the concrete writer explicitly documents that behavior.

### `append_data(frames)`

`append_data` adds one or more frames after the current final frame.

Required behavior:

- preserve existing stream contents;
- append frames in input order;
- accept a single frame and a batch of frames if both forms are supported and documented;
- require every appended frame to match the configured frame shape and compatible type;
- update the logical frame count by the number of appended frames;
- reject incompatible input without partially appending it.

Appending before `create()` or opening an existing stream must produce a documented lifecycle error, unless the concrete writer explicitly supports implicit creation.

### `close()`

`close()` finalizes pending writes and releases backend resources.

Required behavior:

- make successful writes visible and durable according to the backend's documented guarantees;
- release open handles and locks;
- be idempotent, or raise a documented error on repeated calls;
- leave the writer in a state where further writes fail clearly.

A context-manager form is recommended where the backend holds resources during the writer lifetime.

## Error Contract

Concrete writers should expose predictable, backend-independent error categories, even if the underlying exception types differ:

- invalid configuration;
- unavailable or unwritable output target;
- invalid stream name;
- lifecycle misuse, such as writing before creation or after close;
- shape or rank mismatch;
- incompatible data type;
- attempted overwrite or unsupported append operation.

Errors should identify the failed operation and relevant stream or target without exposing backend internals as the only explanation.

## Data and Ordering Guarantees

- Values written successfully must be readable without loss or silent coercion beyond the documented type policy.
- Frame order must be stable across writes and appends.
- A failed append must not leave a partially appended batch.
- The writer must document whether numeric precision, missing values, metadata, and special values are preserved.

## Backend Adapter Rules

- Keep every class-level and instance-level data attribute private with a single leading underscore; expose required external access through properties.
- Keep backend-specific imports and storage operations inside the concrete writer module.
- Do not expose backend objects through the common writer contract.
- Translate backend errors at the contract boundary where practical.
- Keep stream naming, frame shape, type policy, and lifecycle semantics consistent across writer implementations.
- Document capabilities that cannot be supported by every backend rather than weakening the common behavior silently.

## Contract Test Plan

Add backend-independent tests that can run against each writer implementation through a small factory or fixture:

1. Construction stores the configured target and stream information.
2. Creation initializes an empty, usable stream.
3. `write_data` persists a complete dataset exactly.
4. A second `write_data` follows the documented replacement or rejection policy.
5. `append_data` preserves existing frames and adds a single frame in order.
6. `append_data` adds a batch of frames in order.
7. Shape and rank mismatches are rejected.
8. Type mismatches follow the documented type policy.
9. A failed append does not partially modify the stream.
10. Writes before creation and after close fail clearly.
11. Closing makes data readable and releases resources.
12. Existing-target behavior follows the documented overwrite/open policy.

These tests should assert logical behavior and recovered values, not backend-specific implementation details such as HDF5 resize flags or internal handles.

## Implementation Phases

### Phase 1: Contract and test fixture

- Finalize the frame-shape convention and overwrite policy.
- Define shared exception categories or a translation policy.
- Create contract tests that can be reused by all writer implementations.

### Phase 2: HDF5 writer

- Implement the contract in `HDF5DataWriter`.
- Support complete writes through `write_data`.
- Support ordered frame appends through `append_data`.
- Add HDF5-specific tests only for storage features not covered by the shared contract.

### Phase 3: Additional writers

- Implement other backends behind the same logical contract.
- Run the shared contract suite for every backend.
- Record backend-specific limitations and capability differences.

### Phase 4: Integration

- Route analysis result export through a writer factory or format selection layer.
- Keep analysis code independent of concrete writer classes.
- Document writer selection and lifecycle usage for callers.

## Acceptance Criteria

- A caller can write complete data or append frames without knowing the storage backend.
- `write_data` and `append_data` have distinct, tested semantics.
- All supported writers preserve frame order and reject incompatible shapes consistently.
- Lifecycle misuse and target errors are reported clearly.
- Shared contract tests run against every supported writer.
- Backend-specific tests are limited to backend capabilities rather than duplicated behavior.
