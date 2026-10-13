"""Concrete VTKHDF animation writer for LOP SF FCC trajectories.

This module provides the following public members:
    LopSfFccVtkhdfAnimationWriter: Stream validated molecular trajectory
        frames to a VTKHDF 2.6 temporal PolyData file.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, Self

import h5py  # type: ignore[import-untyped]
import numpy as np

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    SPATIAL_DIMENSION,
    VTKHDF_DATASET_TYPE,
    VTKHDF_VERSION,
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
    LopSfFccVtkhdfAnimationWriterState,
)

_PROJECT_METADATA = "LOPSFFCC"
_VTKHDF = "VTKHDF"
_POINT_DATA = "PointData"
_FIELD_DATA = "FieldData"
_STEPS = "Steps"
_LOP_SF_FCC = "lop_sf_fcc"
_STEP_NUMBER = "step_number"
_BOX_LENGTHS = "box_lengths"
_BOX_ANGLES = "box_angles"
_TOPOLOGIES = ("Vertices", "Lines", "Polygons", "Strips")
_TYPE_ATTRIBUTE = "Type"
_VERSION_ATTRIBUTE = "Version"
_N_STEPS_ATTRIBUTE = "NSteps"
_SCALARS_ATTRIBUTE = "Attribute"
_SCALARS_VALUE = "Scalars"
_ANGLE_UNITS = "degrees"
_STAGING_SUFFIX = ".tmp"
_COUNT_DTYPE = np.dtype("int64")
_TIME_DTYPE = np.dtype("float64")
_TOPOLOGY_COUNT = len(_TOPOLOGIES)
_FRAME_DATASET_NAMES = (
    _STEP_NUMBER,
    "positions",
    _LOP_SF_FCC,
    _BOX_LENGTHS,
    _BOX_ANGLES,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationWriter:
    """Stream LOP SF FCC frames to temporal VTKHDF PolyData.

    Creation writes to a same-directory staging file and publishes the final
    target only after a successful close. Append mode validates the complete
    committed schema before accepting additional frames.
    """

    __slots__ = (
        "_file",
        "_file_path",
        "_layout",
        "_metadata",
        "_publishes_on_close",
        "_staging_path",
    )

    def __init__(
        self,
        file_path: str | Path,
        metadata: LopSfFccVtkhdfAnimationMetadata,
        layout: LopSfFccVtkhdfAnimationLayout,
    ) -> None:
        """Initialize the writer.

        Args:
            file_path: Final ``.vtkhdf`` output path.
            metadata: Animation provenance and physical units.
            layout: VTKHDF array dtypes and storage configuration.

        Raises:
            DataWriterConfigurationError: If writer state is invalid.
        """
        state = LopSfFccVtkhdfAnimationWriterState(
            file_path,
            metadata,
            layout,
        )
        state.validate_state()
        self._file_path = state.file_path
        self._metadata = metadata
        self._layout = layout
        self._staging_path = self._file_path.with_name(
            f"{self._file_path.name}{_STAGING_SUFFIX}"
        )
        self._file: h5py.File | None = None
        self._publishes_on_close = False

    @property
    def configuration(self) -> Mapping[str, Any]:
        """Return an independent mapping of writer configuration."""
        return {
            "file_path": self._file_path,
            "staging_path": self._staging_path,
            "vtkhdf_version": self._layout.vtkhdf_version,
            "dataset_type": self._layout.dataset_type,
            "number_of_atoms": self._layout.number_of_atoms,
            "dataset_dtypes": self._layout.dataset_dtypes,
            "chunk_shapes": self._layout.chunk_shapes,
            "compression": self._layout.compression,
            "compression_options": self._layout.compression_options,
            "metadata": self._metadata.as_attributes(),
        }

    def create(self) -> None:
        """Create a staged empty VTKHDF target.

        Raises:
            DataWriterTargetError: If the final or staging target exists or
                the staged schema cannot be created.
        """
        self.close()
        if self._file_path.exists():
            raise DataWriterTargetError(
                f"VTKHDF target already exists: '{self._file_path}'"
            )
        if self._staging_path.exists():
            raise DataWriterTargetError(
                f"VTKHDF staging target already exists: '{self._staging_path}'"
            )
        try:
            self._file = h5py.File(self._staging_path, "x")
            self._publishes_on_close = True
            _create_schema(self._file, self._metadata, self._layout)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self._abort_open_file()
            raise DataWriterTargetError(
                f"could not create VTKHDF target '{self._file_path}'"
            ) from error

    def open_for_append(self) -> None:
        """Open and validate an existing final target for appending.

        Raises:
            DataWriterTargetError: If the target is missing, unreadable, or
                not a VTKHDF PolyData file.
            DataWriterConfigurationError: If the VTKHDF schema or configured
                metadata and layout are incompatible.
        """
        self.close()
        try:
            self._file = h5py.File(self._file_path, "r+")
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            raise DataWriterTargetError(
                f"could not open VTKHDF target '{self._file_path}' for appending"
            ) from error
        try:
            _require_vtkhdf_identity(self._file, self._file_path)
            _require_matching_schema(
                self._file,
                self._file_path,
                self._metadata,
                self._layout,
            )
            self._publishes_on_close = False
        except DataWriterConfigurationError, DataWriterTargetError:
            self._abort_open_file()
            raise

    def append_frames(
        self,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Append one frame or a batch of frames.

        Args:
            step_numbers: Non-negative, strictly increasing simulation steps.
            positions: Point coordinates with shape ``(frames, atoms, 3)``.
            lop_sf_fcc_values: Scalar point data with shape
                ``(frames, atoms)``.
            box_lengths: Positive box lengths with shape ``(frames, 3)``.
            box_angles: Box angles in degrees with shape ``(frames, 3)``.

        Raises:
            DataWriterLifecycleError: If no target is open.
            DataWriterConfigurationError: If frame data is incompatible.
            DataWriterTargetError: If persistent mutation fails.
        """
        target = self._require_file()
        frames = _validated_frames(
            step_numbers,
            positions,
            lop_sf_fcc_values,
            box_lengths,
            box_angles,
            self._metadata,
            self._layout,
        )
        committed_steps = int(target[_VTKHDF][_STEPS].attrs[_N_STEPS_ATTRIBUTE])
        _require_steps_follow_target(target, frames[_STEP_NUMBER], committed_steps)
        try:
            _append_validated_frames(
                target,
                frames,
                committed_steps,
                self._layout,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self._abort_open_file()
            raise DataWriterTargetError(
                f"could not append frames to VTKHDF target '{self._file_path}'"
            ) from error

    def close(self) -> None:
        """Flush, close, and publish a staged target; idempotent when closed."""
        target = self._file
        if target is None:
            return
        publish = self._publishes_on_close
        self._file = None
        self._publishes_on_close = False
        try:
            target.flush()
            target.close()
            if publish:
                self._publish_staging_target()
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            _close_after_failure(target, self._file_path)
            if publish:
                _remove_file_if_present(self._staging_path)
            raise DataWriterTargetError(
                f"could not finalize VTKHDF target '{self._file_path}'"
            ) from error

    def abort(self) -> None:
        """Close without publishing and remove this writer's staging target."""
        target = self._file
        publish = self._publishes_on_close
        self._file = None
        self._publishes_on_close = False
        try:
            if target is not None:
                target.close()
            if publish:
                _remove_file_if_present(self._staging_path)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            raise DataWriterTargetError(
                f"could not abort VTKHDF target '{self._file_path}'"
            ) from error

    def __enter__(self) -> Self:
        """Create a staged target if closed and return this writer."""
        if self._file is None:
            self.create()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Publish on success or abort staged output after an exception."""
        if exception_type is None:
            self.close()
        else:
            self.abort()

    def _require_file(self) -> h5py.File:
        if self._file is None or not self._file.id.valid:
            raise DataWriterLifecycleError(
                "writer must be created or opened before writing"
            )
        return self._file

    def _publish_staging_target(self) -> None:
        try:
            os.link(self._staging_path, self._file_path)
            os.unlink(self._staging_path)
        except OSError:
            _remove_file_if_present(self._staging_path)
            raise

    def _abort_open_file(self) -> None:
        target = self._file
        publish = self._publishes_on_close
        self._file = None
        self._publishes_on_close = False
        if target is not None:
            _close_after_failure(target, self._file_path)
        if publish:
            _remove_file_if_present(self._staging_path)


# ----------
# Private members
# ----------
def _create_schema(
    target: h5py.File,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    project = target.create_group(_PROJECT_METADATA)
    for name, value in metadata.as_attributes().items():
        project.attrs[name] = value

    vtkhdf = target.create_group(_VTKHDF)
    vtkhdf.attrs[_TYPE_ATTRIBUTE] = np.bytes_(VTKHDF_DATASET_TYPE)
    vtkhdf.attrs[_VERSION_ATTRIBUTE] = np.asarray(VTKHDF_VERSION, dtype=np.int64)

    _create_dataset(
        vtkhdf, "NumberOfPoints", (), _COUNT_DTYPE, (layout.frames_per_chunk,), layout
    )
    _create_dataset(
        vtkhdf,
        "Points",
        (SPATIAL_DIMENSION,),
        np.dtype(layout.position_dtype),
        layout.chunk_shapes["points"],
        layout,
    )

    point_data = vtkhdf.create_group(_POINT_DATA)
    lop = _create_dataset(
        point_data,
        _LOP_SF_FCC,
        (),
        np.dtype(layout.lop_sf_fcc_dtype),
        layout.chunk_shapes[_LOP_SF_FCC],
        layout,
    )
    lop.attrs[_SCALARS_ATTRIBUTE] = np.bytes_(_SCALARS_VALUE)

    field_data = vtkhdf.create_group(_FIELD_DATA)
    step = _create_dataset(
        field_data,
        _STEP_NUMBER,
        (),
        np.dtype(layout.step_dtype),
        layout.chunk_shapes[_STEP_NUMBER],
        layout,
    )
    step.attrs["units"] = np.bytes_("step")
    lengths = _create_dataset(
        field_data,
        _BOX_LENGTHS,
        (SPATIAL_DIMENSION,),
        np.dtype(layout.box_dtype),
        layout.chunk_shapes[_BOX_LENGTHS],
        layout,
    )
    lengths.attrs["units"] = np.bytes_(metadata.length_units_label)
    angles = _create_dataset(
        field_data,
        _BOX_ANGLES,
        (SPATIAL_DIMENSION,),
        np.dtype(layout.box_dtype),
        layout.chunk_shapes[_BOX_ANGLES],
        layout,
    )
    angles.attrs["units"] = np.bytes_(_ANGLE_UNITS)

    for topology in _TOPOLOGIES:
        _create_topology(vtkhdf, topology, layout)

    steps = vtkhdf.create_group(_STEPS)
    steps.attrs[_N_STEPS_ATTRIBUTE] = np.int64(0)
    values = _create_dataset(
        steps,
        "Values",
        (),
        _TIME_DTYPE,
        layout.chunk_shapes["time"],
        layout,
    )
    values.attrs["units"] = np.bytes_(metadata.time_units_label)
    for name in ("PartOffsets", "NumberOfParts", "PointOffsets"):
        _create_dataset(
            steps,
            name,
            (),
            _COUNT_DTYPE,
            (layout.frames_per_chunk,),
            layout,
        )
    for name in ("CellOffsets", "ConnectivityIdOffsets"):
        _create_dataset(
            steps,
            name,
            (_TOPOLOGY_COUNT,),
            _COUNT_DTYPE,
            (layout.frames_per_chunk, _TOPOLOGY_COUNT),
            layout,
        )

    point_offsets = steps.create_group("PointDataOffsets")
    _create_dataset(
        point_offsets,
        _LOP_SF_FCC,
        (),
        _COUNT_DTYPE,
        (layout.frames_per_chunk,),
        layout,
    )
    for group_name in ("FieldDataOffsets", "FieldDataSizes"):
        group = steps.create_group(group_name)
        trailing_shape = () if group_name.endswith("Offsets") else (2,)
        chunks = (
            (layout.frames_per_chunk,)
            if not trailing_shape
            else (layout.frames_per_chunk, 2)
        )
        for name in (_STEP_NUMBER, _BOX_LENGTHS, _BOX_ANGLES):
            _create_dataset(
                group,
                name,
                trailing_shape,
                _COUNT_DTYPE,
                chunks,
                layout,
            )


def _create_topology(
    vtkhdf: h5py.Group,
    topology_name: str,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    topology = vtkhdf.create_group(topology_name)
    for name in ("NumberOfCells", "NumberOfConnectivityIds"):
        _create_dataset(
            topology,
            name,
            (),
            _COUNT_DTYPE,
            (layout.frames_per_chunk,),
            layout,
        )
    atom_chunk = layout.atoms_per_chunk_used
    _create_dataset(
        topology,
        "Connectivity",
        (),
        _COUNT_DTYPE,
        (atom_chunk,),
        layout,
    )
    _create_dataset(
        topology,
        "Offsets",
        (),
        _COUNT_DTYPE,
        (atom_chunk + 1,),
        layout,
    )


def _create_dataset(
    parent: h5py.Group,
    name: str,
    trailing_shape: tuple[int, ...],
    dtype: np.dtype[Any],
    chunks: tuple[int, ...],
    layout: LopSfFccVtkhdfAnimationLayout,
) -> h5py.Dataset:
    options: dict[str, Any] = {
        "shape": (0, *trailing_shape),
        "maxshape": (None, *trailing_shape),
        "dtype": dtype,
        "chunks": chunks,
    }
    if layout.compression is not None:
        options["compression"] = layout.compression
        options["compression_opts"] = layout.compression_options
    return parent.create_dataset(name, **options)


def _validated_frames(
    step_numbers: Any,
    positions: Any,
    lop_sf_fcc_values: Any,
    box_lengths: Any,
    box_angles: Any,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> dict[str, np.ndarray[Any, Any]]:
    inputs = {
        _STEP_NUMBER: step_numbers,
        "positions": positions,
        _LOP_SF_FCC: lop_sf_fcc_values,
        _BOX_LENGTHS: box_lengths,
        _BOX_ANGLES: box_angles,
    }
    frame_shapes = {
        _STEP_NUMBER: (),
        "positions": (layout.number_of_atoms, SPATIAL_DIMENSION),
        _LOP_SF_FCC: (layout.number_of_atoms,),
        _BOX_LENGTHS: (SPATIAL_DIMENSION,),
        _BOX_ANGLES: (SPATIAL_DIMENSION,),
    }
    dtypes = {
        _STEP_NUMBER: layout.step_dtype,
        "positions": layout.position_dtype,
        _LOP_SF_FCC: layout.lop_sf_fcc_dtype,
        _BOX_LENGTHS: layout.box_dtype,
        _BOX_ANGLES: layout.box_dtype,
    }
    frames: dict[str, np.ndarray[Any, Any]] = {}
    frame_counts: set[int] = set()
    for name in _FRAME_DATASET_NAMES:
        values = _as_frame_batch(name, inputs[name], frame_shapes[name])
        cast_values = _cast_values(name, values, dtypes[name])
        frames[name] = cast_values
        frame_counts.add(cast_values.shape[0])
    if len(frame_counts) != 1:
        raise DataWriterConfigurationError(
            f"frame counts differ across inputs: {sorted(frame_counts)}"
        )
    frame_count = next(iter(frame_counts))
    if frame_count < 1:
        raise DataWriterConfigurationError("at least one frame is required")
    _require_valid_steps(frames[_STEP_NUMBER])
    _require_finite_array(frames["positions"], "positions")
    _require_finite_array(frames[_LOP_SF_FCC], _LOP_SF_FCC)
    _require_valid_box(frames[_BOX_LENGTHS], frames[_BOX_ANGLES])
    physical_time = frames[_STEP_NUMBER].astype(_TIME_DTYPE) * metadata.time_step
    _require_finite_array(physical_time, "physical time")
    frames["time"] = physical_time
    return frames


def _as_frame_batch(
    name: str,
    value: Any,
    frame_shape: tuple[int, ...],
) -> np.ndarray[Any, Any]:
    values = np.asarray(value)
    frame_rank = len(frame_shape)
    if values.ndim == frame_rank:
        values = values.reshape((1, *values.shape))
    if values.ndim != frame_rank + 1:
        raise DataWriterConfigurationError(
            f"{name} rank {values.ndim} is incompatible with frame shape {frame_shape}"
        )
    if values.shape[1:] != frame_shape:
        raise DataWriterConfigurationError(
            f"{name} shape {values.shape} does not match frame shape {frame_shape}"
        )
    return values


def _cast_values(
    name: str,
    values: np.ndarray[Any, Any],
    dtype_name: str,
) -> np.ndarray[Any, Any]:
    target = np.dtype(dtype_name)
    casting: Literal["safe", "same_kind"] = (
        "safe" if target.kind in "iu" else "same_kind"
    )
    if not np.can_cast(values.dtype, target, casting=casting):
        raise DataWriterConfigurationError(
            f"{name} dtype {values.dtype} cannot be cast to {target} "
            f"with {casting} casting"
        )
    return values.astype(target, copy=False)


def _require_valid_steps(step_numbers: np.ndarray[Any, Any]) -> None:
    if np.any(step_numbers < 0):
        raise DataWriterConfigurationError("step numbers must be non-negative")
    if step_numbers.shape[0] > 1 and np.any(np.diff(step_numbers) <= 0):
        raise DataWriterConfigurationError("step numbers must be strictly increasing")


def _require_finite_array(values: np.ndarray[Any, Any], name: str) -> None:
    if not np.all(np.isfinite(values)):
        raise DataWriterConfigurationError(f"{name} must be finite")


def _require_valid_box(
    box_lengths: np.ndarray[Any, Any],
    box_angles: np.ndarray[Any, Any],
) -> None:
    if not np.all(np.isfinite(box_lengths)) or np.any(box_lengths <= 0):
        raise DataWriterConfigurationError("box lengths must be positive and finite")
    if not np.all(np.isfinite(box_angles)):
        raise DataWriterConfigurationError("box angles must be finite")
    if np.any(box_angles <= 0) or np.any(box_angles >= 180):
        raise DataWriterConfigurationError(
            "box angles must be strictly between 0 and 180 degrees"
        )


def _require_steps_follow_target(
    target: h5py.File,
    step_numbers: np.ndarray[Any, Any],
    committed_steps: int,
) -> None:
    if committed_steps == 0:
        return
    stored = target[_VTKHDF][_FIELD_DATA][_STEP_NUMBER]
    last_stored = int(stored[committed_steps - 1])
    if int(step_numbers[0]) <= last_stored:
        raise DataWriterConfigurationError(
            f"step number {int(step_numbers[0])} does not follow stored "
            f"step number {last_stored}"
        )


def _append_validated_frames(
    target: h5py.File,
    frames: dict[str, np.ndarray[Any, Any]],
    committed_steps: int,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    vtkhdf = target[_VTKHDF]
    steps = vtkhdf[_STEPS]
    frame_count = frames[_STEP_NUMBER].shape[0]
    new_step_count = committed_steps + frame_count
    atom_count = layout.number_of_atoms
    step_indices = np.arange(committed_steps, new_step_count, dtype=_COUNT_DTYPE)
    point_offsets = step_indices * atom_count
    zeros = np.zeros(frame_count, dtype=_COUNT_DTYPE)
    ones = np.ones(frame_count, dtype=_COUNT_DTYPE)
    atom_counts = np.full(frame_count, atom_count, dtype=_COUNT_DTYPE)

    writes = {
        vtkhdf["NumberOfPoints"]: atom_counts,
        vtkhdf["Points"]: frames["positions"].reshape(
            frame_count * atom_count,
            SPATIAL_DIMENSION,
        ),
        vtkhdf[_POINT_DATA][_LOP_SF_FCC]: frames[_LOP_SF_FCC].reshape(
            frame_count * atom_count
        ),
        vtkhdf[_FIELD_DATA][_STEP_NUMBER]: frames[_STEP_NUMBER],
        vtkhdf[_FIELD_DATA][_BOX_LENGTHS]: frames[_BOX_LENGTHS],
        vtkhdf[_FIELD_DATA][_BOX_ANGLES]: frames[_BOX_ANGLES],
        steps["Values"]: frames["time"],
        steps["PartOffsets"]: step_indices,
        steps["NumberOfParts"]: ones,
        steps["PointOffsets"]: point_offsets,
        steps["PointDataOffsets"][_LOP_SF_FCC]: point_offsets,
    }
    for dataset, values in writes.items():
        _append_dataset(dataset, values)

    connectivity = np.tile(
        np.arange(atom_count, dtype=_COUNT_DTYPE),
        frame_count,
    )
    offsets = np.tile(
        np.arange(atom_count + 1, dtype=_COUNT_DTYPE),
        frame_count,
    )
    vertices = vtkhdf["Vertices"]
    _append_dataset(vertices["NumberOfCells"], atom_counts)
    _append_dataset(vertices["NumberOfConnectivityIds"], atom_counts)
    _append_dataset(vertices["Connectivity"], connectivity)
    _append_dataset(vertices["Offsets"], offsets)

    for topology_name in _TOPOLOGIES[1:]:
        topology = vtkhdf[topology_name]
        _append_dataset(topology["NumberOfCells"], zeros)
        _append_dataset(topology["NumberOfConnectivityIds"], zeros)
        _append_dataset(topology["Offsets"], zeros)

    topology_offsets = np.zeros(
        (frame_count, _TOPOLOGY_COUNT),
        dtype=_COUNT_DTYPE,
    )
    topology_offsets[:, 0] = point_offsets
    _append_dataset(steps["CellOffsets"], topology_offsets)
    _append_dataset(steps["ConnectivityIdOffsets"], topology_offsets)

    for name in (_STEP_NUMBER, _BOX_LENGTHS, _BOX_ANGLES):
        _append_dataset(steps["FieldDataOffsets"][name], step_indices)
    _append_dataset(
        steps["FieldDataSizes"][_STEP_NUMBER],
        np.tile(np.asarray([1, 1], dtype=_COUNT_DTYPE), (frame_count, 1)),
    )
    field_vector_sizes = np.tile(
        np.asarray([SPATIAL_DIMENSION, 1], dtype=_COUNT_DTYPE),
        (frame_count, 1),
    )
    _append_dataset(steps["FieldDataSizes"][_BOX_LENGTHS], field_vector_sizes)
    _append_dataset(steps["FieldDataSizes"][_BOX_ANGLES], field_vector_sizes)

    target.flush()
    steps.attrs[_N_STEPS_ATTRIBUTE] = np.int64(new_step_count)
    target.flush()


def _append_dataset(
    dataset: h5py.Dataset,
    values: np.ndarray[Any, Any],
) -> None:
    old_size = dataset.shape[0]
    new_size = old_size + values.shape[0]
    dataset.resize((new_size, *dataset.shape[1:]))
    dataset[old_size:new_size] = values


def _require_vtkhdf_identity(target: h5py.File, file_path: Path) -> None:
    if _VTKHDF not in target or not isinstance(target[_VTKHDF], h5py.Group):
        raise DataWriterTargetError(f"target '{file_path}' has no VTKHDF root group")
    vtkhdf = target[_VTKHDF]
    stored_type = _normalize_attribute(vtkhdf.attrs.get(_TYPE_ATTRIBUTE))
    if stored_type != VTKHDF_DATASET_TYPE:
        raise DataWriterTargetError(
            f"target '{file_path}' is not VTKHDF {VTKHDF_DATASET_TYPE}"
        )
    if _VERSION_ATTRIBUTE not in vtkhdf.attrs:
        raise DataWriterTargetError(
            f"target '{file_path}' has no VTKHDF version attribute"
        )
    version_values = np.asarray(vtkhdf.attrs[_VERSION_ATTRIBUTE])
    if version_values.shape != (2,):
        raise DataWriterTargetError(
            f"target '{file_path}' has an invalid VTKHDF version attribute"
        )


def _require_matching_schema(
    target: h5py.File,
    file_path: Path,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    if _PROJECT_METADATA not in target:
        raise DataWriterConfigurationError(
            f"target '{file_path}' has no {_PROJECT_METADATA} metadata group"
        )
    project = target[_PROJECT_METADATA]
    for name, expected in metadata.as_attributes().items():
        if name not in project.attrs:
            raise DataWriterConfigurationError(
                f"target '{file_path}' is missing metadata attribute '{name}'"
            )
        if _normalize_attribute(project.attrs[name]) != _normalize_attribute(expected):
            raise DataWriterConfigurationError(
                f"target '{file_path}' metadata attribute '{name}' is incompatible"
            )

    vtkhdf = target[_VTKHDF]
    version = tuple(int(value) for value in vtkhdf.attrs[_VERSION_ATTRIBUTE])
    if version != VTKHDF_VERSION:
        raise DataWriterConfigurationError(
            f"target '{file_path}' has VTKHDF version {version}, "
            f"expected {VTKHDF_VERSION}"
        )
    if _STEPS not in vtkhdf:
        raise DataWriterConfigurationError(
            f"target '{file_path}' has no VTKHDF Steps group"
        )
    steps = vtkhdf[_STEPS]
    if _N_STEPS_ATTRIBUTE not in steps.attrs:
        raise DataWriterConfigurationError(
            f"target '{file_path}' has no Steps/{_N_STEPS_ATTRIBUTE}"
        )
    stored_step_count = steps.attrs[_N_STEPS_ATTRIBUTE]
    if not isinstance(stored_step_count, (int, np.integer)) or isinstance(
        stored_step_count,
        bool,
    ):
        raise DataWriterConfigurationError("NSteps must be an integer")
    committed_steps = int(stored_step_count)
    if committed_steps < 0:
        raise DataWriterConfigurationError("NSteps must be non-negative")

    _require_schema_datasets(vtkhdf, committed_steps, layout)
    _require_schema_attributes(vtkhdf, metadata)
    _require_committed_values(vtkhdf, committed_steps, metadata, layout)


def _require_schema_datasets(
    vtkhdf: h5py.Group,
    committed_steps: int,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    atom_count = layout.number_of_atoms
    dataset_specs: dict[str, tuple[tuple[int, ...], np.dtype[Any]]] = {
        "NumberOfPoints": ((committed_steps,), _COUNT_DTYPE),
        "Points": (
            (committed_steps * atom_count, SPATIAL_DIMENSION),
            np.dtype(layout.position_dtype),
        ),
        f"{_POINT_DATA}/{_LOP_SF_FCC}": (
            (committed_steps * atom_count,),
            np.dtype(layout.lop_sf_fcc_dtype),
        ),
        f"{_FIELD_DATA}/{_STEP_NUMBER}": (
            (committed_steps,),
            np.dtype(layout.step_dtype),
        ),
        f"{_FIELD_DATA}/{_BOX_LENGTHS}": (
            (committed_steps, SPATIAL_DIMENSION),
            np.dtype(layout.box_dtype),
        ),
        f"{_FIELD_DATA}/{_BOX_ANGLES}": (
            (committed_steps, SPATIAL_DIMENSION),
            np.dtype(layout.box_dtype),
        ),
        f"{_STEPS}/Values": ((committed_steps,), _TIME_DTYPE),
        f"{_STEPS}/PartOffsets": ((committed_steps,), _COUNT_DTYPE),
        f"{_STEPS}/NumberOfParts": ((committed_steps,), _COUNT_DTYPE),
        f"{_STEPS}/PointOffsets": ((committed_steps,), _COUNT_DTYPE),
        f"{_STEPS}/CellOffsets": (
            (committed_steps, _TOPOLOGY_COUNT),
            _COUNT_DTYPE,
        ),
        f"{_STEPS}/ConnectivityIdOffsets": (
            (committed_steps, _TOPOLOGY_COUNT),
            _COUNT_DTYPE,
        ),
        f"{_STEPS}/PointDataOffsets/{_LOP_SF_FCC}": (
            (committed_steps,),
            _COUNT_DTYPE,
        ),
    }
    for name in (_STEP_NUMBER, _BOX_LENGTHS, _BOX_ANGLES):
        dataset_specs[f"{_STEPS}/FieldDataOffsets/{name}"] = (
            (committed_steps,),
            _COUNT_DTYPE,
        )
        dataset_specs[f"{_STEPS}/FieldDataSizes/{name}"] = (
            (committed_steps, 2),
            _COUNT_DTYPE,
        )
    for topology_name in _TOPOLOGIES:
        connectivity_count = (
            committed_steps * atom_count if topology_name == "Vertices" else 0
        )
        offset_count = (
            committed_steps * (atom_count + 1)
            if topology_name == "Vertices"
            else committed_steps
        )
        for name in ("NumberOfCells", "NumberOfConnectivityIds"):
            dataset_specs[f"{topology_name}/{name}"] = (
                (committed_steps,),
                _COUNT_DTYPE,
            )
        dataset_specs[f"{topology_name}/Connectivity"] = (
            (connectivity_count,),
            _COUNT_DTYPE,
        )
        dataset_specs[f"{topology_name}/Offsets"] = (
            (offset_count,),
            _COUNT_DTYPE,
        )

    for path, (expected_shape, expected_dtype) in dataset_specs.items():
        if path not in vtkhdf or not isinstance(vtkhdf[path], h5py.Dataset):
            raise DataWriterConfigurationError(
                f"VTKHDF target is missing dataset '{path}'"
            )
        dataset = vtkhdf[path]
        if dataset.shape != expected_shape or dataset.dtype != expected_dtype:
            raise DataWriterConfigurationError(
                f"dataset '{path}' has shape {dataset.shape} and dtype "
                f"{dataset.dtype}, expected {expected_shape} and "
                f"{expected_dtype}"
            )
        if dataset.maxshape != (None, *expected_shape[1:]):
            raise DataWriterConfigurationError(
                f"dataset '{path}' is not resizable along its leading axis"
            )
        if dataset.compression != layout.compression:
            raise DataWriterConfigurationError(
                f"dataset '{path}' compression is incompatible"
            )
        if (
            layout.compression_options is not None
            and dataset.compression_opts != layout.compression_options
        ):
            raise DataWriterConfigurationError(
                f"dataset '{path}' compression options are incompatible"
            )
        expected_chunks = _expected_chunks(path, layout)
        if dataset.chunks != expected_chunks:
            raise DataWriterConfigurationError(
                f"dataset '{path}' has chunks {dataset.chunks}, expected "
                f"{expected_chunks}"
            )


def _expected_chunks(
    path: str,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> tuple[int, ...]:
    if path == "Points":
        return layout.chunk_shapes["points"]
    if path == f"{_POINT_DATA}/{_LOP_SF_FCC}":
        return layout.chunk_shapes[_LOP_SF_FCC]
    if path in (
        f"{_FIELD_DATA}/{_BOX_LENGTHS}",
        f"{_FIELD_DATA}/{_BOX_ANGLES}",
    ):
        return layout.chunk_shapes[path.rsplit("/", maxsplit=1)[1]]
    if path == f"{_FIELD_DATA}/{_STEP_NUMBER}":
        return layout.chunk_shapes[_STEP_NUMBER]
    if path == f"{_STEPS}/Values":
        return layout.chunk_shapes["time"]
    if path in (
        f"{_STEPS}/CellOffsets",
        f"{_STEPS}/ConnectivityIdOffsets",
    ):
        return (layout.frames_per_chunk, _TOPOLOGY_COUNT)
    if "/FieldDataSizes/" in path:
        return (layout.frames_per_chunk, 2)
    if path.endswith("/Connectivity"):
        return (layout.atoms_per_chunk_used,)
    if path.endswith("/Offsets") and path.split("/", maxsplit=1)[0] in _TOPOLOGIES:
        return (layout.atoms_per_chunk_used + 1,)
    return (layout.frames_per_chunk,)


def _require_schema_attributes(
    vtkhdf: h5py.Group,
    metadata: LopSfFccVtkhdfAnimationMetadata,
) -> None:
    expected_attributes = {
        f"{_POINT_DATA}/{_LOP_SF_FCC}": {
            _SCALARS_ATTRIBUTE: _SCALARS_VALUE,
        },
        f"{_FIELD_DATA}/{_STEP_NUMBER}": {"units": "step"},
        f"{_FIELD_DATA}/{_BOX_LENGTHS}": {
            "units": metadata.length_units_label,
        },
        f"{_FIELD_DATA}/{_BOX_ANGLES}": {"units": _ANGLE_UNITS},
        f"{_STEPS}/Values": {"units": metadata.time_units_label},
    }
    for path, attributes in expected_attributes.items():
        dataset = vtkhdf[path]
        for name, expected in attributes.items():
            if _normalize_attribute(dataset.attrs.get(name)) != expected:
                raise DataWriterConfigurationError(
                    f"dataset '{path}' attribute '{name}' is incompatible"
                )


def _require_committed_values(
    vtkhdf: h5py.Group,
    committed_steps: int,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> None:
    atom_count = layout.number_of_atoms
    steps = vtkhdf[_STEPS]
    expected_step_indices = np.arange(committed_steps, dtype=_COUNT_DTYPE)
    expected_point_offsets = expected_step_indices * atom_count
    expected_atom_counts = np.full(
        committed_steps,
        atom_count,
        dtype=_COUNT_DTYPE,
    )
    _require_array_equal(
        vtkhdf["NumberOfPoints"],
        expected_atom_counts,
        "NumberOfPoints",
    )
    _require_array_equal(
        steps["PartOffsets"],
        expected_step_indices,
        "Steps/PartOffsets",
    )
    _require_array_equal(
        steps["NumberOfParts"],
        np.ones(committed_steps, dtype=_COUNT_DTYPE),
        "Steps/NumberOfParts",
    )
    _require_array_equal(
        steps["PointOffsets"],
        expected_point_offsets,
        "Steps/PointOffsets",
    )
    _require_array_equal(
        steps["PointDataOffsets"][_LOP_SF_FCC],
        expected_point_offsets,
        f"Steps/PointDataOffsets/{_LOP_SF_FCC}",
    )
    for name in (_STEP_NUMBER, _BOX_LENGTHS, _BOX_ANGLES):
        _require_array_equal(
            steps["FieldDataOffsets"][name],
            expected_step_indices,
            f"Steps/FieldDataOffsets/{name}",
        )
    topology_offsets = np.zeros(
        (committed_steps, _TOPOLOGY_COUNT),
        dtype=_COUNT_DTYPE,
    )
    topology_offsets[:, 0] = expected_point_offsets
    _require_array_equal(
        steps["CellOffsets"],
        topology_offsets,
        "Steps/CellOffsets",
    )
    _require_array_equal(
        steps["ConnectivityIdOffsets"],
        topology_offsets,
        "Steps/ConnectivityIdOffsets",
    )
    vertices = vtkhdf["Vertices"]
    _require_array_equal(
        vertices["NumberOfCells"],
        expected_atom_counts,
        "Vertices/NumberOfCells",
    )
    _require_array_equal(
        vertices["NumberOfConnectivityIds"],
        expected_atom_counts,
        "Vertices/NumberOfConnectivityIds",
    )
    zeros = np.zeros(committed_steps, dtype=_COUNT_DTYPE)
    for topology_name in _TOPOLOGIES[1:]:
        topology = vtkhdf[topology_name]
        _require_array_equal(
            topology["NumberOfCells"],
            zeros,
            f"{topology_name}/NumberOfCells",
        )
        _require_array_equal(
            topology["NumberOfConnectivityIds"],
            zeros,
            f"{topology_name}/NumberOfConnectivityIds",
        )
        _require_array_equal(
            topology["Offsets"],
            zeros,
            f"{topology_name}/Offsets",
        )
    step_sizes = np.tile(
        np.asarray([1, 1], dtype=_COUNT_DTYPE),
        (committed_steps, 1),
    )
    vector_sizes = np.tile(
        np.asarray([SPATIAL_DIMENSION, 1], dtype=_COUNT_DTYPE),
        (committed_steps, 1),
    )
    _require_array_equal(
        steps["FieldDataSizes"][_STEP_NUMBER],
        step_sizes,
        f"Steps/FieldDataSizes/{_STEP_NUMBER}",
    )
    for name in (_BOX_LENGTHS, _BOX_ANGLES):
        _require_array_equal(
            steps["FieldDataSizes"][name],
            vector_sizes,
            f"Steps/FieldDataSizes/{name}",
        )
    stored_steps = vtkhdf[_FIELD_DATA][_STEP_NUMBER][...]
    expected_times = stored_steps.astype(_TIME_DTYPE) * metadata.time_step
    if not np.all(np.isfinite(expected_times)):
        raise DataWriterConfigurationError("stored physical times are not finite")
    _require_array_equal(steps["Values"], expected_times, "Steps/Values")
    if committed_steps > 1:
        if np.any(np.diff(stored_steps) <= 0):
            raise DataWriterConfigurationError(
                "stored step numbers are not strictly increasing"
            )
        stored_times = steps["Values"][...]
        if np.any(np.diff(stored_times) <= 0):
            raise DataWriterConfigurationError(
                "stored physical times are not strictly increasing"
            )


def _require_array_equal(
    dataset: h5py.Dataset,
    expected: np.ndarray[Any, Any],
    name: str,
) -> None:
    if not np.array_equal(dataset[...], expected):
        raise DataWriterConfigurationError(
            f"dataset '{name}' contains incompatible committed values"
        )


def _normalize_attribute(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode()
    if isinstance(value, np.ndarray):
        return tuple(_normalize_attribute(item) for item in value.tolist())
    if isinstance(value, np.generic):
        return _normalize_attribute(value.item())
    if isinstance(value, list | tuple):
        return tuple(_normalize_attribute(item) for item in value)
    return value


def _close_after_failure(target: h5py.File, file_path: Path) -> None:
    try:
        target.close()
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise DataWriterTargetError(
            f"could not close failed VTKHDF target '{file_path}'"
        ) from error


def _remove_file_if_present(path: Path) -> None:
    path.unlink(missing_ok=True)


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
