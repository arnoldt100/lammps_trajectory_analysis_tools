"""Fixtures for backend-independent VTKHDF writer state tests."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object import (
    LopSfFccVtkhdfAnimationWriterValueObject,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)

WRITER_BUILDER_KEY = "test_lop_sf_fcc_vtkhdf_animation_writer"


class StubWriterProduct:
    """Backend-free concrete writer stand-in."""

    def __init__(self, **arguments: Any) -> None:
        """Initialize the stand-in with forwarded builder arguments."""
        self._arguments = arguments
        self._aborted = False
        self._append_count = 0
        self._closed = False
        self._created = False
        self._opened_for_append = False

    @property
    def arguments(self) -> dict[str, Any]:
        """Return an independent mapping of builder arguments."""
        return dict(self._arguments)

    @property
    def created(self) -> bool:
        """Return whether ``create`` was called."""
        return self._created

    @property
    def opened_for_append(self) -> bool:
        """Return whether ``open_for_append`` was called."""
        return self._opened_for_append

    @property
    def configuration(self) -> dict[str, Any]:
        """Return observable stand-in state."""
        return {
            **self._arguments,
            "aborted": self._aborted,
            "append_count": self._append_count,
            "closed": self._closed,
            "created": self._created,
            "opened_for_append": self._opened_for_append,
        }

    def create(self) -> None:
        """Record target creation."""
        self._created = True

    def open_for_append(self) -> None:
        """Record append opening."""
        self._opened_for_append = True

    def append_frames(self, *args: Any, **kwargs: Any) -> None:
        """Record one append call."""
        self._append_count += 1

    def close(self) -> None:
        """Record successful close."""
        self._closed = True

    def abort(self) -> None:
        """Record abort."""
        self._aborted = True


@pytest.fixture
def metadata() -> LopSfFccVtkhdfAnimationMetadata:
    """Return valid immutable animation metadata."""
    return LopSfFccVtkhdfAnimationMetadata(
        time_step=0.002,
        time_units_label="ps",
        length_units_label="angstrom",
        generation_date=datetime(2026, 9, 3, 12, 0, tzinfo=UTC),
        compiler_build_flags=("-O3", "-march=native"),
        generating_machine="nimzoindian",
        lmod_modules=("gcc/13.2.0", "openmpi/4.1.6"),
    )


@pytest.fixture
def layout() -> LopSfFccVtkhdfAnimationLayout:
    """Return a valid immutable animation layout."""
    return LopSfFccVtkhdfAnimationLayout(number_of_atoms=4)


@pytest.fixture
def file_path(tmp_path: Path) -> Path:
    """Return a valid VTKHDF target path."""
    return tmp_path / "lop_sf_fcc_animation.vtkhdf"


@pytest.fixture
def state(
    file_path: Path,
    metadata: LopSfFccVtkhdfAnimationMetadata,
    layout: LopSfFccVtkhdfAnimationLayout,
) -> LopSfFccVtkhdfAnimationWriterState:
    """Return valid closed writer state."""
    return LopSfFccVtkhdfAnimationWriterState(file_path, metadata, layout)


@pytest.fixture
def stub_writer() -> StubWriterProduct:
    """Return an unattached backend-free writer stand-in."""
    return StubWriterProduct()


@pytest.fixture
def stub_registry() -> BuilderRegistry[Any]:
    """Return a registry containing only the writer stand-in."""
    registry: BuilderRegistry[Any] = BuilderRegistry()
    registry.register_builder(WRITER_BUILDER_KEY, StubWriterProduct)
    return registry


@pytest.fixture
def behavior(
    stub_registry: BuilderRegistry[Any],
) -> LopSfFccVtkhdfAnimationWriterValueObjectBehavior:
    """Return behavior using the backend-free registry."""
    return LopSfFccVtkhdfAnimationWriterValueObjectBehavior(
        stub_registry,
        WRITER_BUILDER_KEY,
    )


@pytest.fixture
def value_object(
    state: LopSfFccVtkhdfAnimationWriterState,
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
) -> Iterator[LopSfFccVtkhdfAnimationWriterValueObject]:
    """Return a backend-free writer value object."""
    value = LopSfFccVtkhdfAnimationWriterValueObject(state, behavior)
    yield value
    value.abort()
