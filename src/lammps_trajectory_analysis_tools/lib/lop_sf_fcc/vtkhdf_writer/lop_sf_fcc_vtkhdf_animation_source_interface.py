"""Source contract for LOP SF FCC VTKHDF animation conversion.

This module provides the following public members:
    LopSfFccVtkhdfAnimationFrame: One immutable decoded animation frame.
    LopSfFccVtkhdfAnimationSourceInterface: Interface for validated sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from types import TracebackType
from typing import Any, Self

import numpy as np

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    SPATIAL_DIMENSION,
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationFrame:
    """Immutable decoded values for one animation step."""

    __slots__ = (
        "_box_angles",
        "_box_lengths",
        "_lop_sf_fcc_values",
        "_positions",
        "_step_number",
    )

    def __init__(
        self,
        step_number: int,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Initialize and validate one decoded source frame.

        Args:
            step_number: Non-negative simulation step number.
            positions: Per-atom Cartesian coordinates.
            lop_sf_fcc_values: Per-atom LOP SF FCC scalar values.
            box_lengths: Three positive periodic-box edge lengths.
            box_angles: Three periodic-box angles in degrees.
        """
        self._step_number = _validated_step(step_number)
        self._positions = _validated_float_array(
            positions,
            "positions",
            dimension=2,
        )
        self._lop_sf_fcc_values = _validated_float_array(
            lop_sf_fcc_values,
            "lop_sf_fcc",
            dimension=1,
        )
        self._box_lengths = _validated_float_array(
            box_lengths,
            "box_lengths",
            dimension=1,
        )
        self._box_angles = _validated_float_array(
            box_angles,
            "box_angles",
            dimension=1,
        )
        self._validate_shapes_and_box()

    @property
    def step_number(self) -> int:
        """Return the simulation step number."""
        return self._step_number

    @property
    def positions(self) -> np.ndarray[Any, Any]:
        """Return an independent copy of the atom positions."""
        return self._positions.copy()

    @property
    def lop_sf_fcc_values(self) -> np.ndarray[Any, Any]:
        """Return an independent copy of the per-atom scalar values."""
        return self._lop_sf_fcc_values.copy()

    @property
    def box_lengths(self) -> np.ndarray[Any, Any]:
        """Return an independent copy of the periodic-box lengths."""
        return self._box_lengths.copy()

    @property
    def box_angles(self) -> np.ndarray[Any, Any]:
        """Return an independent copy of the periodic-box angles."""
        return self._box_angles.copy()

    def _validate_shapes_and_box(self) -> None:
        if self._positions.shape[1] != SPATIAL_DIMENSION:
            raise DataWriterConfigurationError(
                f"positions must have shape (number_of_atoms, {SPATIAL_DIMENSION})"
            )
        if self._lop_sf_fcc_values.shape != (self._positions.shape[0],):
            raise DataWriterConfigurationError(
                "lop_sf_fcc must contain one value per atom"
            )
        expected_box_shape = (SPATIAL_DIMENSION,)
        if self._box_lengths.shape != expected_box_shape:
            raise DataWriterConfigurationError(
                f"box_lengths must have shape {expected_box_shape}"
            )
        if self._box_angles.shape != expected_box_shape:
            raise DataWriterConfigurationError(
                f"box_angles must have shape {expected_box_shape}"
            )
        if np.any(self._box_lengths <= 0):
            raise DataWriterConfigurationError("box lengths must be positive")
        if np.any(self._box_angles <= 0) or np.any(self._box_angles >= 180):
            raise DataWriterConfigurationError(
                "box angles must be strictly between 0 and 180 degrees"
            )


class LopSfFccVtkhdfAnimationSourceInterface(ABC):
    """Interface for a validated source of immutable animation frames."""

    __slots__ = ()

    @property
    @abstractmethod
    def metadata(self) -> LopSfFccVtkhdfAnimationMetadata:
        """Return metadata derived from the open source."""

    @property
    @abstractmethod
    def layout(self) -> LopSfFccVtkhdfAnimationLayout:
        """Return the output layout derived from the open source."""

    @property
    @abstractmethod
    def frame_count(self) -> int:
        """Return the number of populated source frames."""

    @abstractmethod
    def open(self) -> Self:
        """Open and validate the source."""

    @abstractmethod
    def frames(self) -> Iterator[LopSfFccVtkhdfAnimationFrame]:
        """Yield decoded frames in source order."""

    @abstractmethod
    def close(self) -> None:
        """Close the source."""

    @abstractmethod
    def __enter__(self) -> Self:
        """Open the source and return it."""

    @abstractmethod
    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the source when leaving a context."""


# ----------
# Private members
# ----------
def _validated_step(value: Any) -> int:
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise DataWriterConfigurationError("step_number must be an integer")
    step = int(value)
    if step < 0:
        raise DataWriterConfigurationError("step_number must be non-negative")
    return step


def _validated_float_array(
    value: Any,
    name: str,
    *,
    dimension: int,
) -> np.ndarray[Any, Any]:
    array = np.asarray(value)
    if array.ndim != dimension:
        raise DataWriterConfigurationError(
            f"{name} must have rank {dimension}, received rank {array.ndim}"
        )
    if array.dtype.kind != "f":
        raise DataWriterConfigurationError(f"{name} must use a floating dtype")
    if not np.all(np.isfinite(array)):
        raise DataWriterConfigurationError(f"{name} must be finite")
    return np.array(array, copy=True)


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
