"""Shared behavior for LOP SF FCC VTKHDF animation writer values.

This module provides the following public members:
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior: Backend-independent
        operations on VTKHDF animation writer state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationWriterState,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationWriterValueObjectBehavior:
    """Backend-independent behavior for animation writer value objects.

    Lifecycle operations receive already constructed writers. This class
    stores no data and does not import a builder registry or storage backend.
    """

    __slots__ = ()

    def copy_state(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Return an equal state without an attached writer."""
        copied = state.replace({})
        copied.validate_state()
        return copied

    def validate_state(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
    ) -> None:
        """Validate complete writer state."""
        state.validate_state()

    def replace_state(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
        changes: Mapping[str, Any],
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Return a validated, handle-free replacement state."""
        candidate = state.replace(changes)
        candidate.validate_state()
        return candidate

    def update_state(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
        changes: Mapping[str, Any],
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Return a validated update candidate when no writer is open.

        Raises:
            DataWriterLifecycleError: If ``state`` owns a writer resource.
        """
        if state.writer is not None:
            raise DataWriterLifecycleError(
                "cannot update state while the writer is open"
            )
        candidate = state.replace(changes)
        candidate.validate_state()
        return candidate

    def states_equal(
        self,
        left: LopSfFccVtkhdfAnimationWriterState,
        right: LopSfFccVtkhdfAnimationWriterState,
    ) -> bool:
        """Compare output-defining state while ignoring writer resources."""
        return left == right

    def state_repr(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
    ) -> str:
        """Return a writer-free representation of state."""
        return repr(state)

    def hash_state(self, state: LopSfFccVtkhdfAnimationWriterState) -> int:
        """Reject hashing for state owned by a mutable value object.

        Raises:
            TypeError: Always.
        """
        raise TypeError("VTKHDF animation writer state is unhashable")

    def dummy_method(self, owned_object: Any, *args: Any, **kwargs: Any) -> Any:
        """Return the value-semantics template placeholder."""
        return None

    def create(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
        writer: Any,
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Create the supplied writer and return state carrying it."""
        state.validate_state()
        writer.create()
        return state.with_writer(writer)

    def open_for_append(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
        writer: Any,
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Open the supplied writer and return state carrying it."""
        state.validate_state()
        writer.open_for_append()
        return state.with_writer(writer)


# ----------
# Private members
# ----------
def _main() -> None:
    return


if __name__ == "__main__":
    _main()
