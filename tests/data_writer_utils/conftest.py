from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_behavior import (
    LopSfFccTrajectoryWriterBehavior,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
    LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object import (
    HDF5LopSfFccTrajectoryWriterValueObject,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)

FrameFactory = Callable[..., dict[str, np.ndarray]]


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "slow: reduced-scale streaming tests excluded from the default run"
    )


@pytest.fixture
def metadata() -> LopSfFccRunMetadata:
    return LopSfFccRunMetadata(
        time_units=0.002,
        time_units_label="ps",
        number_of_trajectories=3,
        generation_date=datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc),
        compiler_build_flags=("-O3", "-march=native"),
        generating_machine="nimzoindian",
        lmod_modules=("gcc/13.2.0", "openmpi/4.1.6"),
    )


@pytest.fixture
def layout() -> LopSfFccTrajectoryLayout:
    return LopSfFccTrajectoryLayout(number_of_atoms=4)


@pytest.fixture
def file_path(tmp_path: Path) -> Path:
    return tmp_path / "lop_sf_fcc_trajectories.h5"


@pytest.fixture
def state(
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> LopSfFccTrajectoryWriterState:
    return LopSfFccTrajectoryWriterState(file_path, metadata, layout)


@pytest.fixture
def stub_writer() -> Any:
    class _StubWriter:
        pass

    return _StubWriter()


@pytest.fixture
def make_frames(layout: LopSfFccTrajectoryLayout) -> FrameFactory:
    def _make_frames(
        frame_count: int = 1,
        first_step: int = 0,
        step_stride: int = 10,
        offset: float = 0.0,
    ) -> dict[str, np.ndarray]:
        atom_count = layout.number_of_atoms
        steps = first_step + step_stride * np.arange(frame_count, dtype=np.int64)
        positions = offset + np.arange(
            frame_count * atom_count * 3, dtype=np.float64
        ).reshape(frame_count, atom_count, 3)
        lop_sf_fcc_values = offset + np.arange(
            frame_count * atom_count, dtype=np.float64
        ).reshape(frame_count, atom_count)
        box_lengths = np.tile(np.array([10.0, 11.0, 12.0]), (frame_count, 1))
        box_angles = np.tile(np.array([90.0, 90.0, 90.0]), (frame_count, 1))
        return {
            "step_number": steps,
            "positions": positions,
            "lop_sf_fcc": lop_sf_fcc_values,
            "box_lengths": box_lengths,
            "box_angles": box_angles,
        }

    return _make_frames


@pytest.fixture
def writer(
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
) -> HDF5LopSfFccTrajectoryDataWriter:
    return HDF5LopSfFccTrajectoryDataWriter(file_path, metadata, layout)


@pytest.fixture
def created_writer(
    writer: HDF5LopSfFccTrajectoryDataWriter,
) -> HDF5LopSfFccTrajectoryDataWriter:
    writer.create()
    yield writer
    writer.close()


def _write_frames(
    writer: HDF5LopSfFccTrajectoryDataWriter,
    method_name: str,
    trajectory_index: int,
    frames: dict[str, np.ndarray],
) -> None:
    getattr(writer, method_name)(
        trajectory_index,
        frames["step_number"],
        frames["positions"],
        frames["lop_sf_fcc"],
        frames["box_lengths"],
        frames["box_angles"],
    )


@pytest.fixture
def write_frames() -> Callable[..., None]:
    """Return a helper calling a write method with the documented argument order."""
    return _write_frames


WRITER_BUILDER_KEY = "test_hdf5_lop_sf_fcc_trajectory_data_writer"


class StubWriterProduct:
    """Minimal stand-in for the concrete writer, used to prove indirection."""

    def __init__(self, **arguments: Any) -> None:
        self.arguments = arguments
        self.created = False
        self.closed = False

    def create(self) -> None:
        self.created = True

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def stub_registry() -> BuilderRegistry:
    registry: BuilderRegistry = BuilderRegistry()
    registry.register_builder(WRITER_BUILDER_KEY, StubWriterProduct)
    return registry


@pytest.fixture
def hdf5_registry() -> BuilderRegistry:
    registry: BuilderRegistry = BuilderRegistry()
    registry.register_builder(
        WRITER_BUILDER_KEY,
        lambda file_path, metadata, layout: HDF5LopSfFccTrajectoryDataWriter(
            file_path, metadata, layout
        ),
    )
    return registry


@pytest.fixture
def behavior(hdf5_registry: BuilderRegistry) -> LopSfFccTrajectoryWriterBehavior:
    return LopSfFccTrajectoryWriterBehavior(hdf5_registry, WRITER_BUILDER_KEY)


@pytest.fixture
def stub_behavior(stub_registry: BuilderRegistry) -> LopSfFccTrajectoryWriterBehavior:
    return LopSfFccTrajectoryWriterBehavior(stub_registry, WRITER_BUILDER_KEY)


@pytest.fixture
def value_object(
    state: LopSfFccTrajectoryWriterState,
    behavior: LopSfFccTrajectoryWriterBehavior,
) -> HDF5LopSfFccTrajectoryWriterValueObject:
    created = HDF5LopSfFccTrajectoryWriterValueObject(state, behavior)
    yield created
    created.close()
