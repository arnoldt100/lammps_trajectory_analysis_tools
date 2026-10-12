"""Value-object interface for LOP SF FCC VTKHDF animation writers.

This module provides the following public members:
    LopSfFccVtkhdfAnimationWriterValueObjectInterface: Value semantics and
        lifecycle contract for an animation writer owner.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.value_object_interface import (
    ValueObjectInterface,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationWriterValueObjectInterface(ValueObjectInterface):
    """Value-semantics and lifecycle contract for animation writer owners.

    The interface stores no instance data. Concrete implementations own
    private state and a concrete writer resource separately.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        """Return a defensive copy of animation metadata."""
        ...

    @property
    @abstractmethod
    def writer_configuration(self) -> Mapping[str, Any]:
        """Return the active concrete writer configuration."""
        ...

    @abstractmethod
    def replace(self, changes: Any) -> Self:
        """Return a validated, handle-free replacement value."""
        ...

    @abstractmethod
    def update(self, changes: Any) -> None:
        """Apply validated changes while no writer is open."""
        ...

    @abstractmethod
    def create(self) -> None:
        """Create and attach a staged VTKHDF writer."""
        ...

    @abstractmethod
    def open_for_append(self) -> Self:
        """Open an existing compatible VTKHDF target and return self."""
        ...

    @abstractmethod
    def append_frames(
        self,
        step_numbers: Any,
        positions: Any,
        lop_sf_fcc_values: Any,
        box_lengths: Any,
        box_angles: Any,
    ) -> None:
        """Append one validated frame or batch of frames."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Finalize and release the attached writer."""
        ...

    @abstractmethod
    def abort(self) -> None:
        """Release the writer without publishing staged creation."""
        ...

    @abstractmethod
    def __enter__(self) -> Self:
        """Create when closed and return self."""
        ...

    @abstractmethod
    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Finalize on success or abort after an exception."""
        ...


# ----------
# Private members
# ----------
def _main() -> None:
    return


if __name__ == "__main__":
    _main()
