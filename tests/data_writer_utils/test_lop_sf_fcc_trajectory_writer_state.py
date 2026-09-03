from pathlib import Path
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccRunMetadata,
    LopSfFccTrajectoryLayout,
    LopSfFccTrajectoryWriterState,
)


def test_validate_state_accepts_valid_members(
    state: LopSfFccTrajectoryWriterState,
) -> None:
    state.validate_state()


def test_validate_state_rejects_invalid_metadata(
    state: LopSfFccTrajectoryWriterState,
) -> None:
    invalid = state.replace({"metadata": state.metadata.replace({"time_units": 0.0})})

    with pytest.raises(DataWriterConfigurationError):
        invalid.validate_state()


def test_validate_state_rejects_invalid_layout(
    state: LopSfFccTrajectoryWriterState,
) -> None:
    invalid = state.replace({"layout": state.layout.replace({"number_of_atoms": 0})})

    with pytest.raises(DataWriterConfigurationError):
        invalid.validate_state()


def test_states_compare_equal_when_only_the_writer_differs(
    file_path: Path,
    metadata: LopSfFccRunMetadata,
    layout: LopSfFccTrajectoryLayout,
    stub_writer: Any,
) -> None:
    without_writer = LopSfFccTrajectoryWriterState(file_path, metadata, layout)
    with_writer = LopSfFccTrajectoryWriterState(
        file_path, metadata, layout, stub_writer
    )

    assert without_writer == with_writer


def test_states_compare_unequal_on_value_fields(
    state: LopSfFccTrajectoryWriterState, tmp_path: Path
) -> None:
    assert state != state.replace({"file_path": tmp_path / "other.h5"})
    assert state != state.replace(
        {"layout": state.layout.replace({"number_of_atoms": 9})}
    )


def test_repr_omits_the_owned_writer(
    state: LopSfFccTrajectoryWriterState, stub_writer: Any
) -> None:
    representation = repr(state.with_writer(stub_writer))

    assert "_StubWriter" not in representation
    assert "writer" not in representation


def test_state_is_unhashable(state: LopSfFccTrajectoryWriterState) -> None:
    with pytest.raises(TypeError):
        hash(state)


def test_replace_applies_changes_and_drops_the_writer(
    state: LopSfFccTrajectoryWriterState, stub_writer: Any, tmp_path: Path
) -> None:
    target = tmp_path / "replaced.h5"
    replaced = state.with_writer(stub_writer).replace({"file_path": target})

    assert replaced.file_path == target
    assert replaced.writer is None


def test_replace_rejects_unknown_fields(
    state: LopSfFccTrajectoryWriterState,
) -> None:
    with pytest.raises(DataWriterConfigurationError):
        state.replace({"writer": object()})


def test_with_writer_returns_a_state_carrying_the_writer(
    state: LopSfFccTrajectoryWriterState, stub_writer: Any
) -> None:
    carrying = state.with_writer(stub_writer)

    assert carrying.writer is stub_writer
    assert state.writer is None


def test_update_raises_because_the_state_is_immutable(
    state: LopSfFccTrajectoryWriterState,
) -> None:
    with pytest.raises(TypeError):
        state.update({"file_path": Path("other.h5")})


def test_state_attributes_cannot_be_assigned(
    state: LopSfFccTrajectoryWriterState,
) -> None:
    with pytest.raises(AttributeError):
        state.file_path = Path("other.h5")  # type: ignore[misc]
