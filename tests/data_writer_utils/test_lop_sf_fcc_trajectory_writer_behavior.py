from pathlib import Path
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_behavior import (
    LopSfFccTrajectoryWriterBehavior,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state import (
    LopSfFccTrajectoryWriterState,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.protocols import (
    StateValueBehaviorProtocol,
)


def test_behavior_implements_every_protocol_member(
    behavior: LopSfFccTrajectoryWriterBehavior,
) -> None:
    # StateValueBehaviorProtocol is not runtime_checkable, so conformance is
    # checked structurally.
    required = [
        name
        for name in vars(StateValueBehaviorProtocol)
        if not name.startswith("_")
    ]

    assert required
    for name in required:
        assert callable(getattr(behavior, name))


def test_copy_state_drops_the_writer_and_leaves_the_source_untouched(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
    stub_writer: Any,
) -> None:
    carrying = state.with_writer(stub_writer)

    copied = behavior.copy_state(carrying)

    assert copied.writer is None
    assert carrying.writer is stub_writer
    assert copied == carrying


def test_replace_state_returns_a_new_state_without_mutating_the_input(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
    tmp_path: Path,
) -> None:
    target = tmp_path / "replaced.h5"

    replaced = behavior.replace_state(state, {"file_path": target})

    assert replaced.file_path == target
    assert state.file_path != target


def test_update_state_returns_a_candidate_without_mutating_the_input(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    changed_layout = state.layout.replace({"number_of_atoms": 9})

    candidate = behavior.update_state(state, {"layout": changed_layout})

    assert candidate.layout.number_of_atoms == 9
    assert state.layout.number_of_atoms != 9


def test_update_state_does_not_validate_its_candidate(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    candidate = behavior.update_state(
        state, {"layout": state.layout.replace({"number_of_atoms": 0})}
    )

    with pytest.raises(DataWriterConfigurationError):
        behavior.validate_state(candidate)


def test_validate_state_delegates_to_the_state(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    behavior.validate_state(state)

    invalid = state.replace({"metadata": state.metadata.replace({"time_units": -1.0})})
    with pytest.raises(DataWriterConfigurationError):
        behavior.validate_state(invalid)


def test_states_equal_ignores_the_writer(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
    stub_writer: Any,
) -> None:
    assert behavior.states_equal(state, state.with_writer(stub_writer))


def test_state_repr_omits_the_writer(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
    stub_writer: Any,
) -> None:
    assert "_StubWriter" not in behavior.state_repr(state.with_writer(stub_writer))


def test_hash_state_raises(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    with pytest.raises(TypeError):
        behavior.hash_state(state)


def test_dummy_method_returns_the_template_placeholder(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    assert behavior.dummy_method(state) is None


def test_build_writer_uses_the_injected_registry(
    stub_behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    product = stub_behavior.build_writer(state)

    assert type(product).__name__ == "StubWriterProduct"
    assert product.arguments["file_path"] == state.file_path
    assert product.arguments["metadata"] is state.metadata
    assert product.arguments["layout"] is state.layout


def test_build_writer_produces_the_concrete_writer_from_a_real_registry(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    product = behavior.build_writer(state)

    assert isinstance(product, HDF5LopSfFccTrajectoryDataWriter)


def test_create_builds_creates_and_attaches_the_writer(
    stub_behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    created = stub_behavior.create(state)

    assert created.writer.created is True
    assert created == state
    assert state.writer is None


def test_create_makes_a_real_hdf5_target(
    behavior: LopSfFccTrajectoryWriterBehavior,
    state: LopSfFccTrajectoryWriterState,
) -> None:
    created = behavior.create(state)

    try:
        assert state.file_path.exists()
    finally:
        created.writer.close()
