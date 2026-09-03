#! /usr/bin/env python3
"""Value-object interface for the LOP SF FCC trajectory writer.

This module provides the following public members:
    LopSfFccTrajectoryWriterValueObjectInterface: The value-semantics contract
        for an object owning a LOP SF FCC trajectory data writer.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Self

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.value_object_interface import (
    ValueObjectInterface,
)

# ----------
# Public members
# ----------
class LopSfFccTrajectoryWriterValueObjectInterface(ValueObjectInterface):
    """Value-semantics contract for an object owning a trajectory data writer.

    This type defines the required value semantics plus the trajectory writing
    surface. It is an abstract interface and intentionally stores no instance
    data; any concrete implementation must own its own private state.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        """Return a defensive copy of the run metadata."""
        ...

    @property
    @abstractmethod
    def writer_configuration(self) -> Mapping[str, Any]:
        """Return the owned writer's configuration."""
        ...

    @abstractmethod
    def replace(self, changes: Any) -> Self:
        """Return a new value object with state changes applied."""
        ...

    @abstractmethod
    def create(self) -> None:
        """Create the output target and write the run metadata."""
        ...

    @abstractmethod
    def append_trajectory_frames(
        self,
        trajectory_index: int,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Append one frame or a batch of frames to a single trajectory."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Finalize writes and release the owned writer."""
        ...

    @abstractmethod
    def __enter__(self) -> Self:
        """Create the output target and return this value object."""
        ...

    @abstractmethod
    def __exit__(
        self,
        exception_type: Any,
        exception: Any,
        traceback: Any,
    ) -> None:
        """Close the owned writer when leaving a context."""
        ...

# ----------
# Private members
# ----------

def _main() -> None:
    return


if __name__ == "__main__":
    _main()
