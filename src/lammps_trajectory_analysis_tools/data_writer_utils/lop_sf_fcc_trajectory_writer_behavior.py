#! /usr/bin/env python3
"""Shared behavior for LOP SF FCC trajectory writer value objects.

This module provides the following public members:
    LopSfFccTrajectoryWriterBehavior: Stateless behavior operating on
        LopSfFccTrajectoryWriterState instances.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)


# ----------
# Public members
# ----------
class LopSfFccTrajectoryWriterBehavior:
    """Behavior shared by trajectory writer value objects.

    The concrete writer is obtained from an injected builder registry, so this
    behavior never imports a storage backend and stays substitutable in tests.
    """

    __slots__ = ("_writer_builder_key", "_writer_registry")

    def __init__(
        self,
        writer_registry: BuilderRegistry[Any],
        writer_builder_key: str,
    ) -> None:
        """Initialize the behavior.

        Args:
            writer_registry: Registry used to build the concrete data writer.
            writer_builder_key: Key of the concrete data writer builder.
        """
        self._writer_registry = writer_registry
        self._writer_builder_key = writer_builder_key

    @property
    def writer_registry(self) -> BuilderRegistry[Any]:
        """Return the registry used to build the concrete data writer."""
        return self._writer_registry

    @property
    def writer_builder_key(self) -> str:
        """Return the key of the concrete data writer builder."""
        return self._writer_builder_key

    def copy_state(self, state: LopSfFccTrajectoryWriterState) -> Any:
        """Return an independent state that carries no owned writer."""
        return state.replace({})

    def validate_state(self, state: LopSfFccTrajectoryWriterState) -> None:
        """Validate state before it is stored."""
        state.validate_state()

    def replace_state(
        self,
        state: LopSfFccTrajectoryWriterState,
        changes: Mapping[str, Any],
    ) -> Any:
        """Return a replacement state after applying ``changes``."""
        return state.replace(changes)

    def update_state(
        self,
        state: LopSfFccTrajectoryWriterState,
        changes: Mapping[str, Any],
    ) -> Any:
        """Return a candidate updated state after applying ``changes``."""
        return state.replace(changes)

    def states_equal(
        self,
        left: LopSfFccTrajectoryWriterState,
        right: LopSfFccTrajectoryWriterState,
    ) -> bool:
        """Compare two states, ignoring any owned writer."""
        return left == right

    def state_repr(self, state: LopSfFccTrajectoryWriterState) -> str:
        """Return a debugging representation of state."""
        return repr(state)

    def hash_state(self, state: LopSfFccTrajectoryWriterState) -> int:
        """Reject hashing.

        Raises:
            TypeError: Always; writer state is mutable in its owning object.
        """
        raise TypeError("trajectory writer state is unhashable")

    def dummy_method(self, owned_object: Any, *args: Any, **kwargs: Any) -> Any:
        """Return the template placeholder value."""
        return None

    def build_writer(self, state: LopSfFccTrajectoryWriterState) -> Any:
        """Build a concrete data writer for ``state`` through the registry."""
        return self._writer_registry.build(
            self._writer_builder_key,
            file_path=state.file_path,
            metadata=state.metadata,
            layout=state.layout,
        )

    def create(self, state: LopSfFccTrajectoryWriterState) -> Any:
        """Build and create a writer, returning the state that carries it."""
        writer = self.build_writer(state)
        writer.create()
        return state.with_writer(writer)

# ----------
# Private members
# ----------

def _main() -> None:
    return


if __name__ == "__main__":
    _main()
