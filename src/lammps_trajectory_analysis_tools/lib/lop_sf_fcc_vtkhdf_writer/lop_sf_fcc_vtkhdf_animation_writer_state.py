"""Value state for the LOP SF FCC VTKHDF animation writer.

This module provides the following public members:
    VTKHDF_VERSION: Supported VTKHDF major and minor version.
    VTKHDF_DATASET_TYPE: Supported VTK dataset type.
    LopSfFccVtkhdfAnimationMetadata: Immutable animation provenance.
    LopSfFccVtkhdfAnimationLayout: Immutable VTKHDF storage layout.
    LopSfFccVtkhdfAnimationWriterState: Complete writer value state.
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
VTKHDF_VERSION = (2, 6)
VTKHDF_DATASET_TYPE = "PolyData"
LOP_SF_FCC_SOURCE_FORMAT = "lop_sf_fcc_hdf5"
SPATIAL_DIMENSION = 3


class LopSfFccVtkhdfAnimationMetadata:
    """Immutable provenance and units for a VTKHDF animation."""

    __slots__ = (
        "_compiler_build_flags",
        "_generating_machine",
        "_generation_date",
        "_length_units_label",
        "_lmod_modules",
        "_time_step",
        "_time_units_label",
    )

    def __init__(
        self,
        time_step: float,
        time_units_label: str,
        length_units_label: str,
        generation_date: datetime,
        compiler_build_flags: Sequence[str],
        generating_machine: str,
        lmod_modules: Sequence[str],
    ) -> None:
        """Initialize animation metadata.

        Args:
            time_step: Simulation time advanced by one trajectory step.
            time_units_label: Unit label for simulation time.
            length_units_label: Unit label for point and box coordinates.
            generation_date: Timezone-aware source-data generation date.
            compiler_build_flags: Build flags used by the source simulation.
            generating_machine: Machine that generated the source trajectory.
            lmod_modules: Modules loaded when building the simulation binary.
        """
        self._time_step = time_step
        self._time_units_label = time_units_label
        self._length_units_label = length_units_label
        self._generation_date = generation_date
        self._compiler_build_flags = _as_string_tuple(compiler_build_flags)
        self._generating_machine = generating_machine
        self._lmod_modules = _as_string_tuple(lmod_modules)

    @property
    def source_format(self) -> str:
        """Return the fixed source-format identifier."""
        return LOP_SF_FCC_SOURCE_FORMAT

    @property
    def time_step(self) -> float:
        """Return the simulation time advanced by one trajectory step."""
        return self._time_step

    @property
    def time_units_label(self) -> str:
        """Return the simulation-time unit label."""
        return self._time_units_label

    @property
    def length_units_label(self) -> str:
        """Return the point and box length-unit label."""
        return self._length_units_label

    @property
    def generation_date(self) -> datetime:
        """Return the source-data generation date."""
        return self._generation_date

    @property
    def compiler_build_flags(self) -> tuple[str, ...]:
        """Return the source simulation compiler flags."""
        return self._compiler_build_flags

    @property
    def generating_machine(self) -> str:
        """Return the source simulation machine."""
        return self._generating_machine

    @property
    def lmod_modules(self) -> tuple[str, ...]:
        """Return the modules used by the source simulation."""
        return self._lmod_modules

    def validate(self) -> None:
        """Validate all metadata fields.

        Raises:
            DataWriterConfigurationError: If any metadata field is invalid.
        """
        if not isinstance(self._time_step, (int, float)) or isinstance(
            self._time_step, bool
        ):
            raise DataWriterConfigurationError("time_step must be a real number")
        if not isfinite(float(self._time_step)) or self._time_step <= 0:
            raise DataWriterConfigurationError("time_step must be positive and finite")
        _require_non_empty_string(self._time_units_label, "time_units_label")
        _require_non_empty_string(self._length_units_label, "length_units_label")
        if not isinstance(self._generation_date, datetime):
            raise DataWriterConfigurationError("generation_date must be a datetime")
        if self._generation_date.tzinfo is None:
            raise DataWriterConfigurationError("generation_date must be timezone-aware")
        _require_string_entries(
            self._compiler_build_flags,
            "compiler_build_flags",
        )
        _require_non_empty_string(self._generating_machine, "generating_machine")
        _require_string_entries(self._lmod_modules, "lmod_modules")

    def as_attributes(self) -> dict[str, Any]:
        """Return an independent mapping of project metadata attributes."""
        return {
            "source_format": self.source_format,
            "time_step": float(self._time_step),
            "time_units_label": self._time_units_label,
            "length_units_label": self._length_units_label,
            "generation_date": self._generation_date.isoformat(),
            "compiler_build_flags": list(self._compiler_build_flags),
            "generating_machine": self._generating_machine,
            "lmod_modules": list(self._lmod_modules),
        }

    def replace(self, changes: Mapping[str, Any]) -> Self:
        """Return new metadata with ``changes`` applied."""
        arguments = self._as_arguments()
        unknown = set(changes) - set(arguments)
        if unknown:
            raise DataWriterConfigurationError(
                f"unknown metadata fields: {sorted(unknown)}"
            )
        arguments.update(changes)
        return type(self)(**arguments)

    def __eq__(self, other: object) -> bool:
        """Compare metadata field by field."""
        if not isinstance(other, LopSfFccVtkhdfAnimationMetadata):
            return NotImplemented
        return self._identity() == other._identity()

    def __hash__(self) -> int:
        """Return a hash derived from immutable metadata."""
        return hash(self._identity())

    def __repr__(self) -> str:
        """Return a debugging representation of metadata."""
        arguments = ", ".join(
            f"{name}={value!r}" for name, value in self._as_arguments().items()
        )
        return f"{type(self).__name__}({arguments})"

    def _as_arguments(self) -> dict[str, Any]:
        return {
            "time_step": self._time_step,
            "time_units_label": self._time_units_label,
            "length_units_label": self._length_units_label,
            "generation_date": self._generation_date,
            "compiler_build_flags": self._compiler_build_flags,
            "generating_machine": self._generating_machine,
            "lmod_modules": self._lmod_modules,
        }

    def _identity(self) -> tuple[Any, ...]:
        return tuple(self._as_arguments().values())


class LopSfFccVtkhdfAnimationLayout:
    """Immutable VTKHDF PolyData array and storage configuration."""

    __slots__ = (
        "_atoms_per_chunk",
        "_box_dtype",
        "_compression",
        "_compression_options",
        "_frames_per_chunk",
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
        frames_per_chunk: int = 1,
        atoms_per_chunk: int = 32768,
        compression: str | None = None,
        compression_options: int | tuple[int, ...] | None = None,
    ) -> None:
        """Initialize the animation layout.

        Args:
            number_of_atoms: Fixed number of atoms in every animation step.
            position_dtype: Floating NumPy dtype for point coordinates.
            lop_sf_fcc_dtype: Floating NumPy dtype for scalar point data.
            box_dtype: Floating NumPy dtype for box field data.
            step_dtype: Integer NumPy dtype for source step numbers.
            frames_per_chunk: Number of temporal values per metadata chunk.
            atoms_per_chunk: Maximum number of atoms per point-data chunk.
            compression: Optional h5py compression filter name.
            compression_options: Hashable options for ``compression``.
        """
        self._number_of_atoms = number_of_atoms
        self._position_dtype = position_dtype
        self._lop_sf_fcc_dtype = lop_sf_fcc_dtype
        self._box_dtype = box_dtype
        self._step_dtype = step_dtype
        self._frames_per_chunk = frames_per_chunk
        self._atoms_per_chunk = atoms_per_chunk
        self._compression = compression
        self._compression_options = compression_options

    @property
    def vtkhdf_version(self) -> tuple[int, int]:
        """Return the supported VTKHDF version."""
        return VTKHDF_VERSION

    @property
    def dataset_type(self) -> str:
        """Return the supported VTK dataset type."""
        return VTKHDF_DATASET_TYPE

    @property
    def number_of_atoms(self) -> int:
        """Return the fixed atom count."""
        return self._number_of_atoms

    @property
    def position_dtype(self) -> str:
        """Return the point-coordinate dtype name."""
        return self._position_dtype

    @property
    def lop_sf_fcc_dtype(self) -> str:
        """Return the scalar point-data dtype name."""
        return self._lop_sf_fcc_dtype

    @property
    def box_dtype(self) -> str:
        """Return the box field-data dtype name."""
        return self._box_dtype

    @property
    def step_dtype(self) -> str:
        """Return the source step-number dtype name."""
        return self._step_dtype

    @property
    def time_dtype(self) -> str:
        """Return the fixed physical-time dtype name."""
        return "float64"

    @property
    def connectivity_dtype(self) -> str:
        """Return the fixed vertex-connectivity dtype name."""
        return "int64"

    @property
    def frames_per_chunk(self) -> int:
        """Return the temporal metadata chunk length."""
        return self._frames_per_chunk

    @property
    def atoms_per_chunk(self) -> int:
        """Return the configured point-data chunk length."""
        return self._atoms_per_chunk

    @property
    def atoms_per_chunk_used(self) -> int:
        """Return the point-data chunk length clamped to the atom count."""
        return min(self._atoms_per_chunk, self._number_of_atoms)

    @property
    def compression(self) -> str | None:
        """Return the optional compression filter name."""
        return self._compression

    @property
    def compression_options(self) -> int | tuple[int, ...] | None:
        """Return the optional compression settings."""
        return self._compression_options

    @property
    def dataset_dtypes(self) -> dict[str, str]:
        """Return an independent mapping of canonical dataset dtypes."""
        return {
            "points": self._position_dtype,
            "lop_sf_fcc": self._lop_sf_fcc_dtype,
            "box_lengths": self._box_dtype,
            "box_angles": self._box_dtype,
            "step_number": self._step_dtype,
            "time": self.time_dtype,
            "connectivity": self.connectivity_dtype,
            "offset": self.connectivity_dtype,
            "count": self.connectivity_dtype,
        }

    @property
    def chunk_shapes(self) -> dict[str, tuple[int, ...]]:
        """Return an independent mapping of planned resizable chunk shapes."""
        atoms = self.atoms_per_chunk_used
        frames = self._frames_per_chunk
        return {
            "points": (atoms, SPATIAL_DIMENSION),
            "lop_sf_fcc": (atoms,),
            "box_lengths": (frames, SPATIAL_DIMENSION),
            "box_angles": (frames, SPATIAL_DIMENSION),
            "step_number": (frames,),
            "time": (frames,),
        }

    def validate(self) -> None:
        """Validate layout fields and derived storage configuration.

        Raises:
            DataWriterConfigurationError: If any layout field is invalid.
        """
        _require_positive_int(self._number_of_atoms, "number_of_atoms")
        _require_positive_int(self._frames_per_chunk, "frames_per_chunk")
        _require_positive_int(self._atoms_per_chunk, "atoms_per_chunk")
        _require_dtype_kind(self._position_dtype, "position_dtype", "f")
        _require_dtype_kind(self._lop_sf_fcc_dtype, "lop_sf_fcc_dtype", "f")
        _require_dtype_kind(self._box_dtype, "box_dtype", "f")
        _require_dtype_kind(self._step_dtype, "step_dtype", "iu")
        if self._compression is None and self._compression_options is not None:
            raise DataWriterConfigurationError(
                "compression_options requires a compression filter"
            )
        if self._compression is not None:
            _require_non_empty_string(self._compression, "compression")
        if self._compression_options is not None:
            _require_compression_options(self._compression_options)

    def replace(self, changes: Mapping[str, Any]) -> Self:
        """Return a new layout with ``changes`` applied."""
        arguments = self._as_arguments()
        unknown = set(changes) - set(arguments)
        if unknown:
            raise DataWriterConfigurationError(
                f"unknown layout fields: {sorted(unknown)}"
            )
        arguments.update(changes)
        return type(self)(**arguments)

    def __eq__(self, other: object) -> bool:
        """Compare layouts field by field."""
        if not isinstance(other, LopSfFccVtkhdfAnimationLayout):
            return NotImplemented
        return self._identity() == other._identity()

    def __hash__(self) -> int:
        """Return a hash derived from immutable layout fields."""
        return hash(self._identity())

    def __repr__(self) -> str:
        """Return a debugging representation of the layout."""
        arguments = ", ".join(
            f"{name}={value!r}" for name, value in self._as_arguments().items()
        )
        return f"{type(self).__name__}({arguments})"

    def _as_arguments(self) -> dict[str, Any]:
        return {
            "number_of_atoms": self._number_of_atoms,
            "position_dtype": self._position_dtype,
            "lop_sf_fcc_dtype": self._lop_sf_fcc_dtype,
            "box_dtype": self._box_dtype,
            "step_dtype": self._step_dtype,
            "frames_per_chunk": self._frames_per_chunk,
            "atoms_per_chunk": self._atoms_per_chunk,
            "compression": self._compression,
            "compression_options": self._compression_options,
        }

    def _identity(self) -> tuple[Any, ...]:
        return tuple(self._as_arguments().values())


class LopSfFccVtkhdfAnimationWriterState:
    """Complete VTKHDF animation writer state.

    The owned writer is a resource rather than a value. It is excluded from
    equality and representation and is dropped by replacement.
    """

    __slots__ = ("_file_path", "_layout", "_metadata", "_writer")
    __hash__ = None  # type: ignore[assignment]

    def __init__(
        self,
        file_path: str | Path,
        metadata: LopSfFccVtkhdfAnimationMetadata,
        layout: LopSfFccVtkhdfAnimationLayout,
        writer: Any = None,
    ) -> None:
        """Initialize writer state.

        Args:
            file_path: Final ``.vtkhdf`` output path.
            metadata: Immutable animation provenance and units.
            layout: Immutable VTKHDF array and storage layout.
            writer: Optional concrete writer resource.
        """
        self._file_path = Path(file_path)
        self._metadata = metadata
        self._layout = layout
        self._writer = writer

    @property
    def file_path(self) -> Path:
        """Return the final VTKHDF output path."""
        return self._file_path

    @property
    def metadata(self) -> LopSfFccVtkhdfAnimationMetadata:
        """Return immutable animation metadata."""
        return self._metadata

    @property
    def layout(self) -> LopSfFccVtkhdfAnimationLayout:
        """Return the immutable animation layout."""
        return self._layout

    @property
    def writer(self) -> Any:
        """Return the concrete writer resource, if one is attached."""
        return self._writer

    def validate_state(self) -> None:
        """Validate the complete writer state.

        Raises:
            DataWriterConfigurationError: If path, metadata, or layout is
                invalid.
        """
        if self._file_path.name in ("", "."):
            raise DataWriterConfigurationError("file_path must name a target")
        if self._file_path.suffix.lower() != ".vtkhdf":
            raise DataWriterConfigurationError(
                "file_path must use the '.vtkhdf' extension"
            )
        if not isinstance(self._metadata, LopSfFccVtkhdfAnimationMetadata):
            raise DataWriterConfigurationError(
                "metadata must be a LopSfFccVtkhdfAnimationMetadata"
            )
        if not isinstance(self._layout, LopSfFccVtkhdfAnimationLayout):
            raise DataWriterConfigurationError(
                "layout must be a LopSfFccVtkhdfAnimationLayout"
            )
        self._metadata.validate()
        self._layout.validate()

    def replace(self, changes: Mapping[str, Any]) -> Self:
        """Return a new state with ``changes`` applied and no writer."""
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
        return type(self)(
            file_path=changes.get("file_path", self._file_path),
            metadata=changes.get("metadata", self._metadata),
            layout=changes.get("layout", self._layout),
            writer=None,
        )

    def with_writer(self, writer: Any) -> Self:
        """Return an otherwise equal state carrying ``writer``."""
        return type(self)(
            self._file_path,
            self._metadata,
            self._layout,
            writer,
        )

    def update(self, changes: Mapping[str, Any]) -> None:
        """Reject in-place mutation.

        Raises:
            TypeError: Always; state is immutable.
        """
        raise TypeError(
            "LopSfFccVtkhdfAnimationWriterState is immutable; use replace()"
        )

    def __eq__(self, other: object) -> bool:
        """Compare output-defining state while ignoring the writer."""
        if not isinstance(other, LopSfFccVtkhdfAnimationWriterState):
            return NotImplemented
        return self._identity() == other._identity()

    def __repr__(self) -> str:
        """Return a representation that omits the writer resource."""
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


def _require_dtype_kind(dtype_name: Any, name: str, kinds: str) -> None:
    try:
        dtype = np.dtype(dtype_name)
    except TypeError as error:
        raise DataWriterConfigurationError(
            f"invalid dtype for {name}: {dtype_name!r}"
        ) from error
    if dtype.kind not in kinds:
        raise DataWriterConfigurationError(
            f"{name} must have NumPy dtype kind in {kinds!r}"
        )


def _require_compression_options(
    options: int | tuple[int, ...],
) -> None:
    values = (options,) if isinstance(options, int) else options
    if isinstance(options, bool) or not values:
        raise DataWriterConfigurationError("compression_options must contain integers")
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        raise DataWriterConfigurationError("compression_options must contain integers")


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
