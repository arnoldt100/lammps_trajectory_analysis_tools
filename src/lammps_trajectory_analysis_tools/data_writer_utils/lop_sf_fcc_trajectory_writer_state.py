#! /usr/bin/env python3
"""Value state for the HDF5 LOP SF FCC trajectory writer.

This module provides the following public members:
    SPATIAL_DIMENSION: The fixed spatial dimension of every simulation.
    MINIMUM_CHUNK_BYTES: The smallest useful HDF5 chunk size.
    MAXIMUM_CHUNK_BYTES: The largest useful HDF5 chunk size.
    LopSfFccRunMetadata: Run provenance stored as HDF5 root attributes.
    LopSfFccTrajectoryLayout: Per-frame geometry and storage tuning.
    LopSfFccTrajectoryWriterState: Complete state owned by the value object.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Any, Self

import numpy as np

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
)

# ----------
# Public members
# ----------
SPATIAL_DIMENSION = 3
MINIMUM_CHUNK_BYTES = 64 * 1024
MAXIMUM_CHUNK_BYTES = 8 * 1024 * 1024


class LopSfFccRunMetadata:
    """Run provenance written as HDF5 root attributes.

    Instances are immutable values: attributes are exposed read-only and
    sequence fields are stored as tuples so that the value stays hashable.
    """

    __slots__ = (
        "_compiler_build_flags",
        "_generating_machine",
        "_generation_date",
        "_lmod_modules",
        "_number_of_trajectories",
        "_time_units",
        "_time_units_label",
    )

    def __init__(
        self,
        time_units: float,
        time_units_label: str,
        number_of_trajectories: int,
        generation_date: datetime,
        compiler_build_flags: Sequence[str],
        generating_machine: str,
        lmod_modules: Sequence[str],
    ) -> None:
        """Initialize the run metadata.

        Args:
            time_units: Simulation time advanced by one trajectory step.
            time_units_label: Unit label for ``time_units``, such as ``"ps"``.
            number_of_trajectories: Fixed number of trajectories in the file.
            generation_date: Timezone-aware date the data was generated.
            compiler_build_flags: Build flags used for the generating binary.
            generating_machine: Machine that generated the trajectory data.
            lmod_modules: Lmod module files loaded when building the binary.
        """
        self._time_units = time_units
        self._time_units_label = time_units_label
        self._number_of_trajectories = number_of_trajectories
        self._generation_date = generation_date
        self._compiler_build_flags = _as_string_tuple(compiler_build_flags)
        self._generating_machine = generating_machine
        self._lmod_modules = _as_string_tuple(lmod_modules)

    @property
    def time_units(self) -> float:
        """Return the simulation time advanced by one trajectory step."""
        return self._time_units

    @property
    def time_units_label(self) -> str:
        """Return the unit label for the time units."""
        return self._time_units_label

    @property
    def number_of_trajectories(self) -> int:
        """Return the fixed number of trajectories in the file."""
        return self._number_of_trajectories

    @property
    def generation_date(self) -> datetime:
        """Return the date the trajectory data was generated."""
        return self._generation_date

    @property
    def compiler_build_flags(self) -> tuple[str, ...]:
        """Return the build flags used for the generating binary."""
        return self._compiler_build_flags

    @property
    def generating_machine(self) -> str:
        """Return the machine that generated the trajectory data."""
        return self._generating_machine

    @property
    def lmod_modules(self) -> tuple[str, ...]:
        """Return the Lmod module files loaded to build the binary."""
        return self._lmod_modules

    def validate(self) -> None:
        """Validate every metadata field.

        Raises:
            DataWriterConfigurationError: If any field is invalid.
        """
        if not isinstance(self._time_units, (int, float)) or isinstance(
            self._time_units, bool
        ):
            raise DataWriterConfigurationError("time_units must be a real number")
        if not isfinite(float(self._time_units)) or self._time_units <= 0:
            raise DataWriterConfigurationError("time_units must be positive and finite")
        _require_non_empty_string(self._time_units_label, "time_units_label")
        if not isinstance(self._number_of_trajectories, int) or isinstance(
            self._number_of_trajectories, bool
        ):
            raise DataWriterConfigurationError("number_of_trajectories must be an int")
        if self._number_of_trajectories <= 0:
            raise DataWriterConfigurationError("number_of_trajectories must be positive")
        if not isinstance(self._generation_date, datetime):
            raise DataWriterConfigurationError("generation_date must be a datetime")
        if self._generation_date.tzinfo is None:
            raise DataWriterConfigurationError("generation_date must be timezone-aware")
        _require_non_empty_string(self._generating_machine, "generating_machine")
        _require_string_entries(self._compiler_build_flags, "compiler_build_flags")
        _require_string_entries(self._lmod_modules, "lmod_modules")

    def as_attributes(self) -> dict[str, Any]:
        """Return an h5py-writable mapping of the metadata."""
        return {
            "time_units": float(self._time_units),
            "time_units_label": self._time_units_label,
            "number_of_trajectories": int(self._number_of_trajectories),
            "generation_date": self._generation_date.isoformat(),
            "compiler_build_flags": list(self._compiler_build_flags),
            "generating_machine": self._generating_machine,
            "lmod_modules": list(self._lmod_modules),
        }

    def replace(self, changes: Mapping[str, Any]) -> Self:
        """Return a new metadata value with ``changes`` applied."""
        return type(self)(**{**self._as_arguments(), **dict(changes)})

    def __eq__(self, other: object) -> bool:
        """Compare metadata values field by field."""
        if not isinstance(other, LopSfFccRunMetadata):
            return NotImplemented
        return self._identity() == other._identity()

    def __hash__(self) -> int:
        """Return a hash derived from every metadata field."""
        return hash(self._identity())

    def __repr__(self) -> str:
        """Return a debugging representation of the metadata."""
        arguments = ", ".join(
            f"{name}={value!r}" for name, value in self._as_arguments().items()
        )
        return f"{type(self).__name__}({arguments})"

    def _as_arguments(self) -> dict[str, Any]:
        return {
            "time_units": self._time_units,
            "time_units_label": self._time_units_label,
            "number_of_trajectories": self._number_of_trajectories,
            "generation_date": self._generation_date,
            "compiler_build_flags": self._compiler_build_flags,
            "generating_machine": self._generating_machine,
            "lmod_modules": self._lmod_modules,
        }

    def _identity(self) -> tuple[Any, ...]:
        return tuple(self._as_arguments().values())


class LopSfFccTrajectoryLayout:
    """Per-frame geometry, dataset types, and HDF5 storage tuning."""

    __slots__ = (
        "_atoms_per_chunk",
        "_box_dtype",
        "_compression",
        "_compression_options",
        "_frames_per_chunk",
        "_length_units_label",
        "_lop_sf_fcc_dtype",
        "_number_of_atoms",
        "_position_dtype",
        "_step_dtype",
    )

    def __init__(
        self,
        number_of_atoms: int,
        position_dtype: str = "float32",
        lop_sf_fcc_dtype: str = "float32",
        box_dtype: str = "float64",
        step_dtype: str = "int64",
        length_units_label: str = "angstrom",
        frames_per_chunk: int = 1,
        atoms_per_chunk: int = 32768,
        compression: str | None = None,
        compression_options: Any = None,
    ) -> None:
        """Initialize the trajectory layout.

        Args:
            number_of_atoms: Number of atoms in every frame.
            position_dtype: NumPy dtype name for the ``positions`` dataset.
            lop_sf_fcc_dtype: NumPy dtype name for the ``lop_sf_fcc`` dataset.
            box_dtype: NumPy dtype name shared by the two box datasets.
            step_dtype: NumPy dtype name for the ``step_number`` dataset.
            length_units_label: Unit label recorded on ``box_lengths``.
            frames_per_chunk: Number of frames spanned by one HDF5 chunk.
            atoms_per_chunk: Number of atoms spanned by one HDF5 chunk.
            compression: Optional h5py compression filter name.
            compression_options: Optional filter options for ``compression``.
        """
        self._number_of_atoms = number_of_atoms
        self._position_dtype = position_dtype
        self._lop_sf_fcc_dtype = lop_sf_fcc_dtype
        self._box_dtype = box_dtype
        self._step_dtype = step_dtype
        self._length_units_label = length_units_label
        self._frames_per_chunk = frames_per_chunk
        self._atoms_per_chunk = atoms_per_chunk
        self._compression = compression
        self._compression_options = compression_options

    @property
    def number_of_atoms(self) -> int:
        """Return the number of atoms in every frame."""
        return self._number_of_atoms

    @property
    def position_dtype(self) -> str:
        """Return the dtype name for the positions dataset."""
        return self._position_dtype

    @property
    def lop_sf_fcc_dtype(self) -> str:
        """Return the dtype name for the LOP SF FCC dataset."""
        return self._lop_sf_fcc_dtype

    @property
    def box_dtype(self) -> str:
        """Return the dtype name shared by the box datasets."""
        return self._box_dtype

    @property
    def step_dtype(self) -> str:
        """Return the dtype name for the step number dataset."""
        return self._step_dtype

    @property
    def length_units_label(self) -> str:
        """Return the unit label recorded on the box lengths dataset."""
        return self._length_units_label

    @property
    def frames_per_chunk(self) -> int:
        """Return the number of frames spanned by one chunk."""
        return self._frames_per_chunk

    @property
    def atoms_per_chunk(self) -> int:
        """Return the number of atoms spanned by one chunk."""
        return self._atoms_per_chunk

    @property
    def compression(self) -> str | None:
        """Return the h5py compression filter name, if any."""
        return self._compression

    @property
    def compression_options(self) -> Any:
        """Return the options for the configured compression filter."""
        return self._compression_options

    @property
    def atoms_per_chunk_used(self) -> int:
        """Return the atom chunk width clamped to the atom count."""
        return min(self._atoms_per_chunk, self._number_of_atoms)

    @property
    def frame_shapes(self) -> dict[str, tuple[int, ...]]:
        """Return the per-frame shape of each dataset, excluding the frame axis."""
        return {
            "positions": (self._number_of_atoms, SPATIAL_DIMENSION),
            "lop_sf_fcc": (self._number_of_atoms,),
            "box_lengths": (SPATIAL_DIMENSION,),
            "box_angles": (SPATIAL_DIMENSION,),
            "step_number": (),
        }

    @property
    def chunk_shapes(self) -> dict[str, tuple[int, ...]]:
        """Return the HDF5 chunk shape of each dataset."""
        frames = self._frames_per_chunk
        atoms = self.atoms_per_chunk_used
        return {
            "positions": (frames, atoms, SPATIAL_DIMENSION),
            "lop_sf_fcc": (frames, atoms),
            "box_lengths": (frames, SPATIAL_DIMENSION),
            "box_angles": (frames, SPATIAL_DIMENSION),
            "step_number": (frames,),
        }

    @property
    def dataset_dtypes(self) -> dict[str, str]:
        """Return the configured dtype name of each dataset."""
        return {
            "positions": self._position_dtype,
            "lop_sf_fcc": self._lop_sf_fcc_dtype,
            "box_lengths": self._box_dtype,
            "box_angles": self._box_dtype,
            "step_number": self._step_dtype,
        }

    def validate(self) -> None:
        """Validate the layout fields and the derived chunk sizes.

        Raises:
            DataWriterConfigurationError: If any field or derived chunk is
                invalid.
        """
        _require_positive_int(self._number_of_atoms, "number_of_atoms")
        _require_positive_int(self._frames_per_chunk, "frames_per_chunk")
        _require_positive_int(self._atoms_per_chunk, "atoms_per_chunk")
        _require_non_empty_string(self._length_units_label, "length_units_label")
        for name, dtype_name in self.dataset_dtypes.items():
            _resolve_dtype(dtype_name, name)
        if self._compression is None and self._compression_options is not None:
            raise DataWriterConfigurationError(
                "compression_options requires a compression filter"
            )
        if self._compression is not None:
            _require_non_empty_string(self._compression, "compression")
        self._validate_chunk_sizes()

    def replace(self, changes: Mapping[str, Any]) -> Self:
        """Return a new layout with ``changes`` applied."""
        return type(self)(**{**self._as_arguments(), **dict(changes)})

    def __eq__(self, other: object) -> bool:
        """Compare layouts field by field."""
        if not isinstance(other, LopSfFccTrajectoryLayout):
            return NotImplemented
        return self._identity() == other._identity()

    def __hash__(self) -> int:
        """Return a hash derived from every layout field."""
        return hash(self._identity())

    def __repr__(self) -> str:
        """Return a debugging representation of the layout."""
        arguments = ", ".join(
            f"{name}={value!r}" for name, value in self._as_arguments().items()
        )
        return f"{type(self).__name__}({arguments})"

    def _validate_chunk_sizes(self) -> None:
        chunk_shapes = self.chunk_shapes
        dtypes = self.dataset_dtypes
        subdivided = self.atoms_per_chunk_used < self._number_of_atoms
        for name in ("positions", "lop_sf_fcc"):
            item_size = _resolve_dtype(dtypes[name], name).itemsize
            chunk_bytes = item_size * int(np.prod(chunk_shapes[name]))
            if chunk_bytes > MAXIMUM_CHUNK_BYTES:
                raise DataWriterConfigurationError(
                    f"{name} chunk of {chunk_bytes} bytes exceeds "
                    f"{MAXIMUM_CHUNK_BYTES} bytes"
                )
            # A chunk below the floor is only wasteful when it needlessly
            # subdivides the atom axis.
            if subdivided and chunk_bytes < MINIMUM_CHUNK_BYTES:
                raise DataWriterConfigurationError(
                    f"{name} chunk of {chunk_bytes} bytes is below "
                    f"{MINIMUM_CHUNK_BYTES} bytes"
                )

    def _as_arguments(self) -> dict[str, Any]:
        return {
            "number_of_atoms": self._number_of_atoms,
            "position_dtype": self._position_dtype,
            "lop_sf_fcc_dtype": self._lop_sf_fcc_dtype,
            "box_dtype": self._box_dtype,
            "step_dtype": self._step_dtype,
            "length_units_label": self._length_units_label,
            "frames_per_chunk": self._frames_per_chunk,
            "atoms_per_chunk": self._atoms_per_chunk,
            "compression": self._compression,
            "compression_options": self._compression_options,
        }

    def _identity(self) -> tuple[Any, ...]:
        return tuple(self._as_arguments().values())


class LopSfFccTrajectoryWriterState:
    """Complete state owned by the trajectory writer value object.

    The owned writer is a resource rather than a value: it is excluded from
    equality and from the debugging representation.
    """

    __slots__ = ("_file_path", "_layout", "_metadata", "_writer")
    __hash__ = None

    def __init__(
        self,
        file_path: str | Path,
        metadata: LopSfFccRunMetadata,
        layout: LopSfFccTrajectoryLayout,
        writer: Any = None,
    ) -> None:
        """Initialize the writer state.

        Args:
            file_path: Path of the HDF5 output target.
            metadata: Run provenance written as root attributes.
            layout: Per-frame geometry and storage tuning.
            writer: Optional owned writer holding the open file handle.
        """
        self._file_path = Path(file_path)
        self._metadata = metadata
        self._layout = layout
        self._writer = writer

    @property
    def file_path(self) -> Path:
        """Return the path of the HDF5 output target."""
        return self._file_path

    @property
    def metadata(self) -> LopSfFccRunMetadata:
        """Return the run metadata."""
        return self._metadata

    @property
    def layout(self) -> LopSfFccTrajectoryLayout:
        """Return the trajectory layout."""
        return self._layout

    @property
    def writer(self) -> Any:
        """Return the owned writer, or ``None`` when no writer is held."""
        return self._writer

    def validate_state(self) -> None:
        """Validate the metadata and layout members.

        Raises:
            DataWriterConfigurationError: If either member is invalid.
        """
        if not isinstance(self._metadata, LopSfFccRunMetadata):
            raise DataWriterConfigurationError(
                "metadata must be a LopSfFccRunMetadata"
            )
        if not isinstance(self._layout, LopSfFccTrajectoryLayout):
            raise DataWriterConfigurationError(
                "layout must be a LopSfFccTrajectoryLayout"
            )
        self._metadata.validate()
        self._layout.validate()

    def replace(self, changes: Mapping[str, Any]) -> Self:
        """Return a new state with ``changes`` applied and no owned writer."""
        arguments = {
            "file_path": self._file_path,
            "metadata": self._metadata,
            "layout": self._layout,
        }
        unknown = set(changes) - set(arguments)
        if unknown:
            raise DataWriterConfigurationError(
                f"unknown state fields: {sorted(unknown)}"
            )
        arguments.update(changes)
        return type(self)(writer=None, **arguments)

    def with_writer(self, writer: Any) -> Self:
        """Return a state identical to this one but carrying ``writer``."""
        return type(self)(
            self._file_path,
            self._metadata,
            self._layout,
            writer,
        )

    def update(self, changes: Mapping[str, Any]) -> None:
        """Reject in-place mutation.

        Raises:
            TypeError: Always; the state is immutable.
        """
        raise TypeError(
            "LopSfFccTrajectoryWriterState is immutable; use replace()"
        )

    def __eq__(self, other: object) -> bool:
        """Compare states by file path, metadata, and layout only."""
        if not isinstance(other, LopSfFccTrajectoryWriterState):
            return NotImplemented
        return self._identity() == other._identity()

    def __repr__(self) -> str:
        """Return a debugging representation that omits the owned writer."""
        return (
            f"{type(self).__name__}(file_path={self._file_path!r}, "
            f"metadata={self._metadata!r}, layout={self._layout!r})"
        )

    def _identity(self) -> tuple[Any, ...]:
        return (self._file_path, self._metadata, self._layout)


# ----------
# Private members
# ----------
def _as_string_tuple(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise DataWriterConfigurationError(
            "expected a sequence of strings, not a single string"
        )
    return tuple(values)


def _require_non_empty_string(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise DataWriterConfigurationError(f"{name} must be a non-empty string")


def _require_string_entries(values: tuple[Any, ...], name: str) -> None:
    if any(not isinstance(value, str) for value in values):
        raise DataWriterConfigurationError(f"{name} entries must be strings")


def _require_positive_int(value: Any, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise DataWriterConfigurationError(f"{name} must be an int")
    if value < 1:
        raise DataWriterConfigurationError(f"{name} must be at least 1")


def _resolve_dtype(dtype_name: Any, dataset_name: str) -> np.dtype:
    try:
        return np.dtype(dtype_name)
    except TypeError as error:
        raise DataWriterConfigurationError(
            f"invalid dtype for {dataset_name}: {dtype_name!r}"
        ) from error


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
