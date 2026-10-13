"""Mutable value object owning a VTKHDF animation writer.

This module provides the following public members:
    LopSfFccVtkhdfAnimationWriterValueObject: Value-oriented lifecycle owner
        for a concrete VTKHDF animation writer.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_interface import (
    LopSfFccVtkhdfAnimationWriterValueObjectInterface,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationWriterValueObject(
    LopSfFccVtkhdfAnimationWriterValueObjectInterface
):
    """Mutable value object owning a concrete VTKHDF writer resource."""

    __slots__ = ("_behavior", "_state_implementations")
    __hash__ = None  # type: ignore[assignment]

    def __init__(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
        behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    ) -> None:
        """Initialize from copied and validated state.

        Args:
            state: Writer state to copy and validate.
            behavior: Shared state and lifecycle behavior.
        """
        self._behavior = behavior
        self._state_implementations = behavior.copy_state(state)

    @property
    def state_implementations(self) -> LopSfFccVtkhdfAnimationWriterState:
        """Return an equal defensive state without the writer resource."""
        return self._behavior.copy_state(self._state_implementations)

    @property
    def state(self) -> LopSfFccVtkhdfAnimationWriterState:
        """Return an equal defensive value state."""
        return self.state_implementations

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Return an independent mapping of animation metadata."""
        return self._state_implementations.metadata.as_attributes()

    @property
    def writer_configuration(self) -> Mapping[str, Any]:
        """Return active concrete writer configuration.

        Raises:
            DataWriterLifecycleError: If no writer is attached.
        """
        return self._require_writer().configuration

    def replace(self, changes: Any) -> Self:
        """Return a validated replacement with no attached writer."""
        updated_state = self._behavior.replace_state(
            self._state_implementations,
            changes,
        )
        return type(self)(updated_state, self._behavior)

    def update(self, changes: Any) -> None:
        """Apply validated changes while no writer is attached.

        Args:
            changes: Mapping of state field names to replacement values.

        Raises:
            DataWriterLifecycleError: If a writer is attached.
        """
        self._state_implementations = self._behavior.update_state(
            self._state_implementations,
            changes,
        )

    def create(self) -> None:
        """Create and attach a staged concrete writer."""
        self.close()
        self._state_implementations = self._behavior.create(self._state_implementations)

    def open_for_append(self) -> Self:
        """Open an existing target for append and return this object."""
        self.close()
        self._state_implementations = self._behavior.open_for_append(
            self._state_implementations
        )
        return self

    def append_frames(
        self,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Append one frame or a batch to the attached writer."""
        self._require_writer().append_frames(
            step_numbers,
            positions,
            lop_sf_fcc_values,
            box_lengths,
            box_angles,
        )

    def close(self) -> None:
        """Finalize and release the attached writer."""
        writer = self._state_implementations.writer
        if writer is not None:
            writer.close()
            self._state_implementations = self._behavior.copy_state(
                self._state_implementations
            )

    def abort(self) -> None:
        """Abort and release the attached writer."""
        writer = self._state_implementations.writer
        if writer is not None:
            writer.abort()
            self._state_implementations = self._behavior.copy_state(
                self._state_implementations
            )

    def dummy_method(self, *args: Any, **kwargs: Any) -> Any:
        """Return the placeholder required by the value template."""
        return self._behavior.dummy_method(
            self._state_implementations,
            *args,
            **kwargs,
        )

    def __enter__(self) -> Self:
        """Create when closed and return this value object."""
        if self._state_implementations.writer is None:
            self.create()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Finalize on success or abort after an exception."""
        if exception_type is None:
            self.close()
        else:
            self.abort()

    def __eq__(self, other: object) -> bool:
        """Compare value state while ignoring attached writer resources."""
        if type(self) is not type(other):
            return NotImplemented
        return self._behavior.states_equal(
            self._state_implementations,
            other._state_implementations,
        )

    def __repr__(self) -> str:
        """Return a writer-free debugging representation."""
        return (
            f"{type(self).__name__}(state="
            f"{self._behavior.state_repr(self._state_implementations)})"
        )

    def _require_writer(self) -> Any:
        writer = self._state_implementations.writer
        if writer is None:
            raise DataWriterLifecycleError(
                "create() or open_for_append() must be called before writing"
            )
        return writer


# ----------
# Private members
# ----------
def _main() -> None:
    return


if __name__ == "__main__":
    _main()
