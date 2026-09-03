#! /usr/bin/env python3
"""Mutable value object owning an HDF5 LOP SF FCC trajectory data writer.

This module provides the following public members:
    HDF5LopSfFccTrajectoryWriterValueObject: Value object that owns a concrete
        trajectory data writer.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_behavior import (
    LopSfFccTrajectoryWriterBehavior,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object_interface import (
    LopSfFccTrajectoryWriterValueObjectInterface,
)

# ----------
# Public members
# ----------
class HDF5LopSfFccTrajectoryWriterValueObject(
    LopSfFccTrajectoryWriterValueObjectInterface
):
    """Mutable value object owning an HDF5 trajectory data writer.

    Value identity is the file path, run metadata, and trajectory layout. The
    owned writer is a resource: it is excluded from equality and never shared
    with a replacement value object.
    """

    __slots__ = ("_behavior", "_state_implementations")
    __hash__ = None

    def __init__(
        self,
        state: LopSfFccTrajectoryWriterState,
        behavior: LopSfFccTrajectoryWriterBehavior,
    ) -> None:
        """Initialize the value object.

        Args:
            state: The writer state to copy and validate.
            behavior: Shared behavior applied to the state.
        """
        self._behavior = behavior
        copied_state = behavior.copy_state(state)
        behavior.validate_state(copied_state)
        self._state_implementations = copied_state

    @property
    def state_implementations(self) -> Any:
        """Return a defensive copy of the concrete state implementations."""
        return self._behavior.copy_state(self._state_implementations)

    @property
    def state(self) -> Any:
        """Return a defensive copy of the value state."""
        return self.state_implementations

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Return a defensive copy of the run metadata."""
        return self._state_implementations.metadata.as_attributes()

    @property
    def writer_configuration(self) -> Mapping[str, Any]:
        """Return the owned writer's configuration.

        Raises:
            DataWriterLifecycleError: If no writer has been created.
        """
        return self._require_writer().configuration

    def replace(self, changes: Any) -> Self:
        """Return a new value object with ``changes`` applied and no writer."""
        updated_state = self._behavior.replace_state(
            self._state_implementations,
            changes,
        )
        return type(self)(updated_state, self._behavior)

    def update(self, changes: Any) -> None:
        """Apply state changes in place when the resulting state is valid.

        Args:
            changes: Mapping of state field names to replacement values.

        Raises:
            DataWriterLifecycleError: If a writer is currently open.
        """
        if self._state_implementations.writer is not None:
            raise DataWriterLifecycleError(
                "cannot update state while the writer is open"
            )
        updated_state = self._behavior.update_state(
            self._state_implementations,
            changes,
        )
        self._behavior.validate_state(updated_state)
        self._state_implementations = updated_state

    def create(self) -> None:
        """Create the output target and write the run metadata."""
        self.close()
        self._state_implementations = self._behavior.create(
            self._state_implementations
        )

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

        Args:
            trajectory_index: Index of the trajectory to extend.
            step_numbers: Step numbers of the frames.
            positions: Atom positions of the frames.
            lop_sf_fcc_values: Per-atom LOP SF FCC values of the frames.
            box_lengths: Simulation box edge lengths of the frames.
            box_angles: Lattice angles, in degrees, of the frames.
        """
        self._require_writer().append_trajectory_frames(
            trajectory_index,
            step_numbers,
            positions,
            lop_sf_fcc_values,
            box_lengths,
            box_angles,
        )

    def close(self) -> None:
        """Close the owned writer and release it from the state."""
        writer = self._state_implementations.writer
        if writer is not None:
            writer.close()
            self._state_implementations = self._behavior.copy_state(
                self._state_implementations
            )

    def dummy_method(self, *args: Any, **kwargs: Any) -> Any:
        """Return the placeholder value required by the template contract."""
        return self._behavior.dummy_method(
            self._state_implementations,
            *args,
            **kwargs,
        )

    def __enter__(self) -> Self:
        """Create the output target and return this value object."""
        self.create()
        return self

    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
        """Close the owned writer when leaving a context."""
        self.close()

    def __eq__(self, other: object) -> bool:
        """Compare value objects by state, ignoring any owned writer."""
        if type(self) is not type(other):
            return NotImplemented
        return self._behavior.states_equal(
            self._state_implementations,
            other._state_implementations,
        )

    def __repr__(self) -> str:
        """Return a debugging representation that omits the owned writer."""
        return (
            f"{type(self).__name__}(state="
            f"{self._behavior.state_repr(self._state_implementations)})"
        )

    def _require_writer(self) -> Any:
        writer = self._state_implementations.writer
        if writer is None:
            raise DataWriterLifecycleError("create() must be called before writing")
        return writer

# ----------
# Private members
# ----------

def _main() -> None:
    return


if __name__ == "__main__":
    _main()
