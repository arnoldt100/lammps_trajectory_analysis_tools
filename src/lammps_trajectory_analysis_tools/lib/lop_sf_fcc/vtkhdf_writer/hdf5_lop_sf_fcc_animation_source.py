"""HDF5 source adapter for LOP SF FCC VTKHDF animation conversion.

This module provides the following public members:
    HDF5LopSfFccAnimationSource: Validate and decode one producer HDF5 file.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import h5py  # type: ignore[import-untyped]
import numpy as np

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_source_interface import (
    LopSfFccVtkhdfAnimationFrame,
    LopSfFccVtkhdfAnimationSourceInterface,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    SPATIAL_DIMENSION,
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
)

_TRAJECTORY_ROOT = "trajectories"
_POSITIONS = "positions"
_LOP_SF_FCC = "lop_sf_fcc"
_BOX_LENGTHS = "box_lengths"
_BOX_ANGLES = "box_angles"
_STEP_NUMBER = "step_number"
_DATASET_NAMES = frozenset(
    {
        _POSITIONS,
        _LOP_SF_FCC,
        _BOX_LENGTHS,
        _BOX_ANGLES,
        _STEP_NUMBER,
    }
)
_ANGLE_UNITS = "degrees"


# ----------
# Public members
# ----------
class HDF5LopSfFccAnimationSource(LopSfFccVtkhdfAnimationSourceInterface):
    """Validate and decode a persisted LOP SF FCC HDF5 trajectory."""

    __slots__ = (
        "_file",
        "_file_path",
        "_frame_group_names",
        "_layout",
        "_metadata",
    )

    def __init__(self, file_path: str | Path) -> None:
        """Initialize a closed source adapter.

        Args:
            file_path: Path to producer HDF5 output.
        """
        self._file_path = Path(file_path)
        self._file: h5py.File | None = None
        self._frame_group_names: tuple[str, ...] = ()
        self._layout: LopSfFccVtkhdfAnimationLayout | None = None
        self._metadata: LopSfFccVtkhdfAnimationMetadata | None = None

    @property
    def file_path(self) -> Path:
        """Return the configured HDF5 source path."""
        return self._file_path

    @property
    def metadata(self) -> LopSfFccVtkhdfAnimationMetadata:
        """Return metadata derived from the open source."""
        self._require_open()
        if self._metadata is None:
            raise DataWriterLifecycleError("source metadata is unavailable")
        return self._metadata

    @property
    def layout(self) -> LopSfFccVtkhdfAnimationLayout:
        """Return the output layout derived from the open source."""
        self._require_open()
        if self._layout is None:
            raise DataWriterLifecycleError("source layout is unavailable")
        return self._layout

    @property
    def frame_count(self) -> int:
        """Return the number of populated source trajectory groups."""
        self._require_open()
        return len(self._frame_group_names)

    def open(self) -> Self:
        """Open and validate the complete producer schema.

        Returns:
            This source adapter.

        Raises:
            DataWriterTargetError: If the source cannot be opened.
            DataWriterConfigurationError: If its schema is incompatible.
        """
        self.close()
        try:
            self._file = h5py.File(self._file_path, "r")
        except (OSError, TypeError, ValueError) as error:
            raise DataWriterTargetError(
                f"could not open HDF5 source '{self._file_path}'"
            ) from error
        try:
            self._validate_source(self._file)
        except DataWriterConfigurationError:
            self.close()
            raise
        except (OSError, TypeError, ValueError) as error:
            self.close()
            raise DataWriterConfigurationError(
                f"invalid HDF5 source '{self._file_path}'"
            ) from error
        return self

    def frames(self) -> Iterator[LopSfFccVtkhdfAnimationFrame]:
        """Yield immutable decoded frames in trajectory-group order."""
        source = self._require_open()
        for group_name in self._frame_group_names:
            try:
                group = source[_TRAJECTORY_ROOT][group_name]
                yield LopSfFccVtkhdfAnimationFrame(
                    step_number=int(group[_STEP_NUMBER][0]),
                    positions=group[_POSITIONS][0],
                    lop_sf_fcc_values=group[_LOP_SF_FCC][0],
                    box_lengths=group[_BOX_LENGTHS][0],
                    box_angles=group[_BOX_ANGLES][0],
                )
            except DataWriterConfigurationError:
                raise
            except (OSError, TypeError, ValueError) as error:
                raise DataWriterTargetError(
                    f"could not decode source frame '{group_name}'"
                ) from error

    def close(self) -> None:
        """Close the source and discard all derived state."""
        if self._file is not None:
            self._file.close()
        self._file = None
        self._frame_group_names = ()
        self._layout = None
        self._metadata = None

    def __enter__(self) -> Self:
        """Open the source and return it."""
        return self.open()

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the source when leaving a context."""
        self.close()

    def _validate_source(self, source: h5py.File) -> None:
        metadata_arguments = self._metadata_arguments(source)
        trajectory_count = _required_positive_int_attribute(
            source.attrs,
            "number_of_trajectories",
        )
        root = _required_group(source, _TRAJECTORY_ROOT)
        expected_names = tuple(f"traj_{index:05d}" for index in range(trajectory_count))
        if set(root.keys()) != set(expected_names):
            raise DataWriterConfigurationError(
                "source trajectory groups do not match number_of_trajectories"
            )

        first_group = _required_group(root, expected_names[0])
        layout_arguments = self._layout_arguments(first_group)
        populated: list[str] = []
        empty_seen = False
        previous_step: int | None = None
        for index, group_name in enumerate(expected_names):
            group = _required_group(root, group_name)
            frame_count = self._validate_group(
                group,
                index,
                layout_arguments,
                metadata_arguments["length_units_label"],
            )
            if frame_count == 0:
                empty_seen = True
                continue
            if empty_seen:
                raise DataWriterConfigurationError(
                    f"populated trajectory '{group_name}' follows an empty group"
                )
            step = int(group[_STEP_NUMBER][0])
            if step < 0:
                raise DataWriterConfigurationError(
                    f"trajectory '{group_name}' has a negative step number"
                )
            if previous_step is not None and step <= previous_step:
                raise DataWriterConfigurationError(
                    "source step numbers must be strictly increasing"
                )
            previous_step = step
            populated.append(group_name)

        metadata = LopSfFccVtkhdfAnimationMetadata(**metadata_arguments)
        layout = LopSfFccVtkhdfAnimationLayout(**layout_arguments)
        metadata.validate()
        layout.validate()
        self._metadata = metadata
        self._layout = layout
        self._frame_group_names = tuple(populated)

    def _metadata_arguments(self, source: h5py.File) -> dict[str, Any]:
        generation_date_text = _required_string_attribute(
            source.attrs,
            "generation_date",
        )
        try:
            generation_date = datetime.fromisoformat(generation_date_text)
        except ValueError as error:
            raise DataWriterConfigurationError(
                "generation_date must be an ISO 8601 datetime"
            ) from error
        root = _required_group(source, _TRAJECTORY_ROOT)
        first_group = _required_group(root, "traj_00000")
        box_lengths = _required_dataset(first_group, _BOX_LENGTHS)
        return {
            "time_step": _required_real_attribute(source.attrs, "time_step"),
            "time_units_label": _required_string_attribute(
                source.attrs,
                "time_units_label",
            ),
            "length_units_label": _required_string_attribute(
                box_lengths.attrs,
                "units",
            ),
            "generation_date": generation_date,
            "compiler_build_flags": _required_string_sequence_attribute(
                source.attrs,
                "compiler_build_flags",
            ),
            "generating_machine": _required_string_attribute(
                source.attrs,
                "generating_machine",
            ),
            "lmod_modules": _required_string_sequence_attribute(
                source.attrs,
                "lmod_modules",
            ),
        }

    def _layout_arguments(self, group: h5py.Group) -> dict[str, Any]:
        if set(group.keys()) != _DATASET_NAMES:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' does not contain the required datasets"
            )
        positions = _required_dataset(group, _POSITIONS)
        lop_sf_fcc = _required_dataset(group, _LOP_SF_FCC)
        box_lengths = _required_dataset(group, _BOX_LENGTHS)
        box_angles = _required_dataset(group, _BOX_ANGLES)
        step_number = _required_dataset(group, _STEP_NUMBER)
        if positions.ndim != 3 or positions.shape[2:] != (SPATIAL_DIMENSION,):
            raise DataWriterConfigurationError(
                "positions must have shape (frames, number_of_atoms, 3)"
            )
        number_of_atoms = int(positions.shape[1])
        if number_of_atoms < 1:
            raise DataWriterConfigurationError("number_of_atoms must be positive")
        _require_dtype_kind(positions, _POSITIONS, "f")
        _require_dtype_kind(lop_sf_fcc, _LOP_SF_FCC, "f")
        _require_dtype_kind(box_lengths, _BOX_LENGTHS, "f")
        _require_dtype_kind(box_angles, _BOX_ANGLES, "f")
        _require_dtype_kind(step_number, _STEP_NUMBER, "iu")
        if box_lengths.dtype != box_angles.dtype:
            raise DataWriterConfigurationError(
                "box_lengths and box_angles must use the same dtype"
            )
        return {
            "number_of_atoms": number_of_atoms,
            "position_dtype": positions.dtype.name,
            "lop_sf_fcc_dtype": lop_sf_fcc.dtype.name,
            "box_dtype": box_lengths.dtype.name,
            "step_dtype": step_number.dtype.name,
        }

    def _validate_group(
        self,
        group: h5py.Group,
        index: int,
        layout: dict[str, Any],
        length_units_label: str,
    ) -> int:
        if set(group.keys()) != _DATASET_NAMES:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' does not contain the required datasets"
            )
        stored_index = _required_integer_attribute(group.attrs, "trajectory_index")
        if stored_index != index:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' has index {stored_index}, expected {index}"
            )
        expected_shapes = {
            _POSITIONS: (
                layout["number_of_atoms"],
                SPATIAL_DIMENSION,
            ),
            _LOP_SF_FCC: (layout["number_of_atoms"],),
            _BOX_LENGTHS: (SPATIAL_DIMENSION,),
            _BOX_ANGLES: (SPATIAL_DIMENSION,),
            _STEP_NUMBER: (),
        }
        expected_dtypes = {
            _POSITIONS: layout["position_dtype"],
            _LOP_SF_FCC: layout["lop_sf_fcc_dtype"],
            _BOX_LENGTHS: layout["box_dtype"],
            _BOX_ANGLES: layout["box_dtype"],
            _STEP_NUMBER: layout["step_dtype"],
        }
        frame_counts: set[int] = set()
        for name in _DATASET_NAMES:
            dataset = _required_dataset(group, name)
            if dataset.shape[1:] != expected_shapes[name]:
                raise DataWriterConfigurationError(
                    f"dataset '{dataset.name}' has incompatible shape {dataset.shape}"
                )
            if dataset.dtype != np.dtype(expected_dtypes[name]):
                raise DataWriterConfigurationError(
                    f"dataset '{dataset.name}' has incompatible dtype {dataset.dtype}"
                )
            frame_counts.add(int(dataset.shape[0]))
        if len(frame_counts) != 1:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' datasets have different frame counts"
            )
        frame_count = frame_counts.pop()
        if frame_count > 1:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' contains more than one frame"
            )
        lengths = _required_dataset(group, _BOX_LENGTHS)
        angles = _required_dataset(group, _BOX_ANGLES)
        if _required_string_attribute(lengths.attrs, "units") != length_units_label:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' has inconsistent length units"
            )
        if _required_string_attribute(angles.attrs, "units") != _ANGLE_UNITS:
            raise DataWriterConfigurationError(
                f"trajectory '{group.name}' box angles must use degrees"
            )
        return frame_count

    def _require_open(self) -> h5py.File:
        if self._file is None or not self._file.id.valid:
            raise DataWriterLifecycleError("source must be opened before reading")
        return self._file


# ----------
# Private members
# ----------
def _required_group(parent: h5py.Group, name: str) -> h5py.Group:
    if name not in parent or not isinstance(parent[name], h5py.Group):
        raise DataWriterConfigurationError(f"missing HDF5 group '{name}'")
    return parent[name]


def _required_dataset(parent: h5py.Group, name: str) -> h5py.Dataset:
    if name not in parent or not isinstance(parent[name], h5py.Dataset):
        raise DataWriterConfigurationError(f"missing HDF5 dataset '{name}'")
    return parent[name]


def _required_attribute(attributes: h5py.AttributeManager, name: str) -> Any:
    if name not in attributes:
        raise DataWriterConfigurationError(f"missing HDF5 attribute '{name}'")
    return attributes[name]


def _required_string_attribute(
    attributes: h5py.AttributeManager,
    name: str,
) -> str:
    value = _required_attribute(attributes, name)
    if isinstance(value, (bytes, np.bytes_)):
        try:
            value = bytes(value).decode("utf-8")
        except UnicodeDecodeError as error:
            raise DataWriterConfigurationError(
                f"HDF5 attribute '{name}' is not valid UTF-8"
            ) from error
    if not isinstance(value, str) or not value:
        raise DataWriterConfigurationError(
            f"HDF5 attribute '{name}' must be a non-empty string"
        )
    return value


def _required_string_sequence_attribute(
    attributes: h5py.AttributeManager,
    name: str,
) -> tuple[str, ...]:
    value = _required_attribute(attributes, name)
    if isinstance(value, (str, bytes, np.bytes_)):
        values = (value,)
    elif isinstance(value, (list, tuple, np.ndarray)):
        values = tuple(value)
    else:
        raise DataWriterConfigurationError(
            f"HDF5 attribute '{name}' must be a string sequence"
        )
    decoded: list[str] = []
    for entry in values:
        if isinstance(entry, (bytes, np.bytes_)):
            try:
                entry = bytes(entry).decode("utf-8")
            except UnicodeDecodeError as error:
                raise DataWriterConfigurationError(
                    f"HDF5 attribute '{name}' contains invalid UTF-8"
                ) from error
        if not isinstance(entry, str):
            raise DataWriterConfigurationError(
                f"HDF5 attribute '{name}' entries must be strings"
            )
        decoded.append(entry)
    return tuple(decoded)


def _required_real_attribute(
    attributes: h5py.AttributeManager,
    name: str,
) -> float:
    value = _required_attribute(attributes, name)
    if not isinstance(value, (int, float, np.integer, np.floating)) or isinstance(
        value,
        (bool, np.bool_),
    ):
        raise DataWriterConfigurationError(
            f"HDF5 attribute '{name}' must be a real number"
        )
    return float(value)


def _required_integer_attribute(
    attributes: h5py.AttributeManager,
    name: str,
) -> int:
    value = _required_attribute(attributes, name)
    if not isinstance(value, (int, np.integer)) or isinstance(
        value,
        (bool, np.bool_),
    ):
        raise DataWriterConfigurationError(
            f"HDF5 attribute '{name}' must be an integer"
        )
    return int(value)


def _required_positive_int_attribute(
    attributes: h5py.AttributeManager,
    name: str,
) -> int:
    value = _required_integer_attribute(attributes, name)
    if value < 1:
        raise DataWriterConfigurationError(f"HDF5 attribute '{name}' must be positive")
    return value


def _require_dtype_kind(
    dataset: h5py.Dataset,
    name: str,
    kinds: str,
) -> None:
    if dataset.dtype.kind not in kinds:
        raise DataWriterConfigurationError(
            f"dataset '{name}' has unsupported dtype {dataset.dtype}"
        )


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
