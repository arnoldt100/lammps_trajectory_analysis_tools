# Concrete Data Writer LOP SF FCC Plan

## Objective

Define an HDF5 specific concrete writer that satisfies the
Data Writer Contract Plan. The contract is in markdown file
`project-top-level/docs/data_writer_contract_plan.md`.

## Core Concepts

- Frame: A frame is one item of an ordered sequence of data.
The data consists of 3 items:

  - A scalar value t, type float64, which is the time of the trajectory.

  - An Numpy array of shape (N,3) of each atom coordinates. The type is float64.

  - An Numpy array of shape (N,1) of type float64. The is the calculated
    Local Order parameter FCC structure factor.

## Proposed Implementation

The concrete writer is to provide following public operations or methods:

```text
LOPSfFCCWriter(output_target, stream_name, frame_shape, data_type)
create()
write_data()
append_data()
close()
```

## Adapter Rules

- Keep every class-level and instance-level data attribute private with a single leading underscore; expose required external access through properties.

- Keep backend-specific imports and storage operations inside the concrete writer module.

- Translate backend errors at the contract boundary where practical.

- Keep stream naming, frame shape, type policy, and lifecycle semantics consistent across writer implementations.

- Document capabilities that cannot be supported by every backend rather than weakening the common behavior silently.

### create()

`create()` prepares a new output target and initializes the named data stream.

Required behavior:

- create the destination if it does not exist;
- initialize an empty stream that can accept frames when appending is supported;
- establish the configured type and frame shape;
- reject invalid configuration or an unusable target with a documented exception.

The writer must refuse to overwrite an existing target.

### `write_data(data)`

`write_data` writes the complete dataset in one operation.

Required behavior:

- accept data whose shape and type satisfy the configured contract;
- replace the stream's current contents, or reject the operation if replacement is not supported; this policy must be documented;
- preserve the complete input data and its ordering;
- avoid silently truncating, reshaping, or dropping values;
- reject incompatible shape, rank, or type with a documented exception.

`write_data` is not an append operation. Calling it with a second complete dataset must not  add frames.

### `append_data(frames)`

### `close()`

## Error Contract

## Data and Ordering Guarantees
