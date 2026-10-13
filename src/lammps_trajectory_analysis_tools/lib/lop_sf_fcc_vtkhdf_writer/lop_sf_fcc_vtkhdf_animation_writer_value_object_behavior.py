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
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationWriterState,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationWriterValueObjectBehavior:
    """Backend-independent behavior for animation writer value objects.

    Concrete writer construction is delegated to an injected builder
    registry, so this module does not import h5py or a VTK backend.
    """

    __slots__ = ("_writer_builder_key", "_writer_registry")

    def __init__(
        self,
        writer_registry: BuilderRegistry[Any],
        writer_builder_key: str,
    ) -> None:
        """Initialize behavior.

        Args:
            writer_registry: Registry that constructs concrete writers.
            writer_builder_key: Registered concrete writer builder key.
        """
        self._writer_registry = writer_registry
        self._writer_builder_key = writer_builder_key

    @property
    def writer_builder_key(self) -> str:
        """Return the concrete writer builder key."""
        return self._writer_builder_key

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

    def build_writer(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
    ) -> Any:
        """Build a concrete writer through the injected registry."""
        state.validate_state()
        return self._writer_registry.build(
            self._writer_builder_key,
            file_path=state.file_path,
            metadata=state.metadata,
            layout=state.layout,
        )

    def create(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Create a concrete writer and return state carrying it."""
        writer = self.build_writer(state)
        writer.create()
        return state.with_writer(writer)

    def open_for_append(
        self,
        state: LopSfFccVtkhdfAnimationWriterState,
    ) -> LopSfFccVtkhdfAnimationWriterState:
        """Open a concrete writer and return state carrying it."""
        writer = self.build_writer(state)
        writer.open_for_append()
        return state.with_writer(writer)


# ----------
# Private members
# ----------
def _main() -> None:
    return


if __name__ == "__main__":
    _main()
