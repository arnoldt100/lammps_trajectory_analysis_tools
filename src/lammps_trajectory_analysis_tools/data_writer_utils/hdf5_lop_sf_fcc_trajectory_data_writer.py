#! /usr/bin/env python3
"""Concrete HDF5 writer for LOP SF FCC molecular dynamics trajectories.

This module provides the following public members:
    HDF5LopSfFccTrajectoryDataWriter: Write a fixed set of trajectories, each
        carrying positions, the per-atom FCC local order parameter structure
        factor, the simulation box, and step numbers, to one HDF5 file.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    SPATIAL_DIMENSION,
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
)

_TRAJECTORY_ROOT = "trajectories"
_POSITIONS = "positions"
_LOP_SF_FCC = "lop_sf_fcc"
_BOX_LENGTHS = "box_lengths"
_BOX_ANGLES = "box_angles"
_STEP_NUMBER = "step_number"
_DATASET_NAMES = (_POSITIONS, _LOP_SF_FCC, _BOX_LENGTHS, _BOX_ANGLES, _STEP_NUMBER)
_ANGLE_UNITS = "degrees"
_MINIMUM_CHUNK_CACHE_BYTES = 1024 * 1024
_CHUNK_CACHE_CHUNKS = 4

# ----------
# Public members
# ----------
class HDF5LopSfFccTrajectoryDataWriter:
    """Write a fixed set of LOP SF FCC trajectories to one HDF5 file.

    ``create`` refuses to overwrite an existing target, writes the run metadata
    as root attributes, and pre-creates one group per trajectory. Frames are
    appended along the leading axis of every dataset in a trajectory group.
    """

    def __init__(
        self,
        file_path: str | Path,
        metadata: LopSfFccRunMetadata,
        layout: LopSfFccTrajectoryLayout,
    ) -> None:
        """Initialize the writer.

        Args:
            file_path: Path of the HDF5 output target.
            metadata: Run provenance written as root attributes.
            layout: Per-frame geometry, dataset types, and storage tuning.

        Raises:
            DataWriterConfigurationError: If the metadata or layout is invalid.
        """
        metadata.validate()
        layout.validate()
        self._file_path = Path(file_path)
        self._metadata = metadata
        self._layout = layout
        self._file: h5py.File | None = None

    @property
    def configuration(self) -> Mapping[str, Any]:
        """Return the configured output target, layout, and metadata."""
        return {
            "file_path": self._file_path,
            "number_of_trajectories": self._metadata.number_of_trajectories,
            "number_of_atoms": self._layout.number_of_atoms,
            "spatial_dimension": SPATIAL_DIMENSION,
            "dataset_dtypes": self._layout.dataset_dtypes,
            "chunk_shapes": self._layout.chunk_shapes,
            "compression": self._layout.compression,
            "compression_options": self._layout.compression_options,
            "metadata": self._metadata.as_attributes(),
        }

    def create(self) -> None:
        """Create the target, write metadata, and pre-create every trajectory.

        Raises:
            DataWriterTargetError: If the target exists or cannot be created.
        """
        self.close()
        try:
            self._file = h5py.File(
                self._file_path,
                "x",
                rdcc_nbytes=self._chunk_cache_bytes(),
            )
            self._write_metadata_attributes(self._file)
            trajectory_root = self._file.create_group(_TRAJECTORY_ROOT)
            for index in range(self._metadata.number_of_trajectories):
                self._create_trajectory_group(trajectory_root, index)
        except (OSError, TypeError, ValueError) as error:
            self.close()
            raise DataWriterTargetError(
                f"could not create HDF5 target '{self._file_path}'"
            ) from error

    def write_trajectory(
        self,
        trajectory_index: int,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Replace one trajectory's frames with a complete dataset.

        This method requires the whole trajectory in memory and is intended for
        small runs; use ``append_trajectory_frames`` for production volumes.

        Args:
            trajectory_index: Index of the trajectory to replace.
            step_numbers: Step numbers of the frames.
            positions: Atom positions of the frames.
            lop_sf_fcc_values: Per-atom LOP SF FCC values of the frames.
            box_lengths: Simulation box edge lengths of the frames.
            box_angles: Lattice angles, in degrees, of the frames.
        """
        group = self._require_group(trajectory_index)
        frames = self._validated_frames(
            step_numbers,
            positions,
            lop_sf_fcc_values,
            box_lengths,
            box_angles,
        )
        frame_count = frames[_STEP_NUMBER].shape[0]
        self._resize_group(group, frame_count)
        for name in _DATASET_NAMES:
            group[name][...] = frames[name]

    def append_trajectory_frames(
        self,
        trajectory_index: int,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Append one frame or a batch of frames to a single trajectory.

        The append is all-or-nothing: every input is validated before any
        dataset is resized or written.

        Args:
            trajectory_index: Index of the trajectory to extend.
            step_numbers: Step numbers of the frames.
            positions: Atom positions of the frames.
            lop_sf_fcc_values: Per-atom LOP SF FCC values of the frames.
            box_lengths: Simulation box edge lengths of the frames.
            box_angles: Lattice angles, in degrees, of the frames.
        """
        group = self._require_group(trajectory_index)
        frames = self._validated_frames(
            step_numbers,
            positions,
            lop_sf_fcc_values,
            box_lengths,
            box_angles,
        )
        old_count = int(group[_STEP_NUMBER].shape[0])
        self._require_increasing_from_stored(group, frames[_STEP_NUMBER], old_count)
        new_count = old_count + frames[_STEP_NUMBER].shape[0]
        self._resize_group(group, new_count)
        for name in _DATASET_NAMES:
            group[name][old_count:] = frames[name]

    def close(self) -> None:
        """Close the HDF5 file and release the handle."""
        if self._file is not None:
            self._file.close()
            self._file = None

    def __enter__(self) -> "HDF5LopSfFccTrajectoryDataWriter":
        """Create the target and return this writer."""
        self.create()
        return self

    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
        """Close the target when leaving a context."""
        self.close()

    # ----------
    # Private methods
    # ----------
    def _chunk_cache_bytes(self) -> int:
        chunk_shapes = self._layout.chunk_shapes
        dtypes = self._layout.dataset_dtypes
        largest = max(
            np.dtype(dtypes[name]).itemsize * int(np.prod(chunk_shapes[name]))
            for name in (_POSITIONS, _LOP_SF_FCC)
        )
        return max(_MINIMUM_CHUNK_CACHE_BYTES, largest * _CHUNK_CACHE_CHUNKS)

    def _write_metadata_attributes(self, target: h5py.File) -> None:
        for name, value in self._metadata.as_attributes().items():
            target.attrs[name] = value

    def _create_trajectory_group(self, root: h5py.Group, index: int) -> h5py.Group:
        group = root.create_group(self._trajectory_name(index))
        group.attrs["trajectory_index"] = index
        frame_shapes = self._layout.frame_shapes
        chunk_shapes = self._layout.chunk_shapes
        dtypes = self._layout.dataset_dtypes
        for name in _DATASET_NAMES:
            frame_shape = frame_shapes[name]
            group.create_dataset(
                name,
                shape=(0, *frame_shape),
                maxshape=(None, *frame_shape),
                dtype=np.dtype(dtypes[name]),
                chunks=chunk_shapes[name],
                compression=self._layout.compression,
                compression_opts=self._layout.compression_options,
            )
        group[_BOX_LENGTHS].attrs["units"] = self._layout.length_units_label
        group[_BOX_ANGLES].attrs["units"] = _ANGLE_UNITS
        return group

    @staticmethod
    def _trajectory_name(index: int) -> str:
        return f"traj_{index:05d}"

    def _require_group(self, trajectory_index: int) -> h5py.Group:
        if self._file is None or not self._file.id.valid:
            raise DataWriterLifecycleError("writer must be created before writing")
        if not isinstance(trajectory_index, (int, np.integer)) or isinstance(
            trajectory_index, bool
        ):
            raise DataWriterConfigurationError("trajectory_index must be an int")
        if not 0 <= trajectory_index < self._metadata.number_of_trajectories:
            raise DataWriterConfigurationError(
                f"trajectory_index {trajectory_index} outside "
                f"[0, {self._metadata.number_of_trajectories})"
            )
        return self._file[_TRAJECTORY_ROOT][self._trajectory_name(int(trajectory_index))]

    def _resize_group(self, group: h5py.Group, frame_count: int) -> None:
        frame_shapes = self._layout.frame_shapes
        for name in _DATASET_NAMES:
            group[name].resize((frame_count, *frame_shapes[name]))

    def _require_increasing_from_stored(
        self,
        group: h5py.Group,
        step_numbers: np.ndarray,
        old_count: int,
    ) -> None:
        if old_count == 0:
            return
        last_stored = int(group[_STEP_NUMBER][old_count - 1])
        if int(step_numbers[0]) <= last_stored:
            raise DataWriterConfigurationError(
                f"step number {int(step_numbers[0])} does not follow the stored "
                f"step number {last_stored}"
            )

    def _validated_frames(
        self,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> dict[str, np.ndarray]:
        inputs = {
            _STEP_NUMBER: step_numbers,
            _POSITIONS: positions,
            _LOP_SF_FCC: lop_sf_fcc_values,
            _BOX_LENGTHS: box_lengths,
            _BOX_ANGLES: box_angles,
        }
        frame_shapes = self._layout.frame_shapes
        dtypes = self._layout.dataset_dtypes
        frames: dict[str, np.ndarray] = {}
        frame_counts: set[int] = set()
        for name, value in inputs.items():
            values = self._as_frame_batch(name, value, frame_shapes[name])
            frames[name] = self._cast_values(name, values, dtypes[name])
            frame_counts.add(values.shape[0])
        if len(frame_counts) != 1:
            raise DataWriterConfigurationError(
                f"frame counts differ across inputs: {sorted(frame_counts)}"
            )
        self._require_valid_steps(frames[_STEP_NUMBER])
        self._require_valid_box(frames[_BOX_LENGTHS], frames[_BOX_ANGLES])
        return frames

    @staticmethod
    def _as_frame_batch(
        name: str,
        value: Any,
        frame_shape: tuple[int, ...],
    ) -> np.ndarray:
        values = np.asarray(value)
        frame_rank = len(frame_shape)
        if values.ndim == frame_rank:
            values = values.reshape((1, *values.shape))
        if values.ndim != frame_rank + 1:
            raise DataWriterConfigurationError(
                f"{name} rank {values.ndim} is incompatible with frame shape "
                f"{frame_shape}"
            )
        if values.shape[1:] != frame_shape:
            raise DataWriterConfigurationError(
                f"{name} shape {values.shape} does not match frame shape "
                f"{frame_shape}"
            )
        return values

    @staticmethod
    def _cast_values(name: str, values: np.ndarray, dtype_name: str) -> np.ndarray:
        target = np.dtype(dtype_name)
        # Storage may be narrower than the analysis dtype, so float datasets
        # allow same-kind narrowing while integer datasets do not.
        casting = "safe" if target.kind in "iu" else "same_kind"
        if not np.can_cast(values.dtype, target, casting=casting):
            raise DataWriterConfigurationError(
                f"{name} dtype {values.dtype} cannot be cast to {target} "
                f"with {casting} casting"
            )
        return values.astype(target, copy=False)

    @staticmethod
    def _require_valid_steps(step_numbers: np.ndarray) -> None:
        if np.any(step_numbers < 0):
            raise DataWriterConfigurationError("step numbers must be non-negative")
        if step_numbers.shape[0] > 1 and np.any(np.diff(step_numbers) <= 0):
            raise DataWriterConfigurationError(
                "step numbers must be strictly increasing"
            )

    @staticmethod
    def _require_valid_box(
        box_lengths: np.ndarray,
        box_angles: np.ndarray,
    ) -> None:
        if not np.all(np.isfinite(box_lengths)) or np.any(box_lengths <= 0):
            raise DataWriterConfigurationError("box lengths must be positive")
        if not np.all(np.isfinite(box_angles)):
            raise DataWriterConfigurationError("box angles must be finite")
        if np.any(box_angles <= 0) or np.any(box_angles >= 180):
            raise DataWriterConfigurationError(
                "box angles must lie strictly between 0 and 180 degrees"
            )

# ----------
# Private members
# ----------

def _main() -> None:
    return


if __name__ == "__main__":
    _main()
