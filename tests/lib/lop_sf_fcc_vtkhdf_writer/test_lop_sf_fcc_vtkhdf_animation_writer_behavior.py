"""Tests for backend-independent VTKHDF writer behavior."""

import ast
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.protocols import (
    StateValueBehaviorProtocol,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)


def test_behavior_implements_the_state_value_protocol(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
) -> None:
    required = [
        name for name in vars(StateValueBehaviorProtocol) if not name.startswith("_")
    ]

    assert required
    for name in required:
        assert callable(getattr(behavior, name))


@pytest.mark.parametrize("attribute", ["_writer_registry", "_writer_builder_key"])
def test_behavior_cannot_store_instance_data(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    attribute: str,
) -> None:
    assert not hasattr(behavior, "__dict__")
    with pytest.raises(AttributeError):
        setattr(behavior, attribute, object())
    assert not hasattr(behavior, "build_writer")


def test_copy_state_is_equal_independent_and_writer_free(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
) -> None:
    carrying = state.with_writer(stub_writer)

    copied = behavior.copy_state(carrying)

    assert copied == carrying
    assert copied is not carrying
    assert copied.writer is None
    assert carrying.writer is stub_writer


def test_replace_state_validates_and_drops_writer(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
    tmp_path: Path,
) -> None:
    replacement = behavior.replace_state(
        state.with_writer(stub_writer),
        {"file_path": tmp_path / "replacement.vtkhdf"},
    )

    assert replacement.file_path == tmp_path / "replacement.vtkhdf"
    assert replacement.writer is None
    with pytest.raises(DataWriterConfigurationError):
        behavior.replace_state(state, {"file_path": tmp_path / "invalid.h5"})


def test_update_state_validates_without_mutating_the_input(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    candidate = behavior.update_state(
        state,
        {"layout": state.layout.replace({"number_of_atoms": 9})},
    )

    assert candidate.layout.number_of_atoms == 9
    assert state.layout.number_of_atoms == 4
    with pytest.raises(DataWriterConfigurationError):
        behavior.update_state(
            state,
            {"layout": state.layout.replace({"number_of_atoms": 0})},
        )


def test_update_state_is_rejected_while_writer_is_open(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
) -> None:
    with pytest.raises(DataWriterLifecycleError, match="writer is open"):
        behavior.update_state(
            state.with_writer(stub_writer),
            {"layout": state.layout.replace({"number_of_atoms": 9})},
        )


def test_equality_and_repr_ignore_writer_resources(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
) -> None:
    carrying = state.with_writer(stub_writer)

    assert behavior.states_equal(state, carrying)
    assert "StubWriterProduct" not in behavior.state_repr(carrying)


def test_hash_state_rejects_mutable_value_state(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    with pytest.raises(TypeError, match="unhashable"):
        behavior.hash_state(state)


def test_dummy_method_returns_the_template_placeholder(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
) -> None:
    assert behavior.dummy_method(state) is None


def test_create_and_open_for_append_attach_stub_writers(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
    writer_builder: Callable[[LopSfFccVtkhdfAnimationWriterState], Any],
) -> None:
    created = behavior.create(state, writer_builder(state))
    opened = behavior.open_for_append(state, writer_builder(state))

    assert created.writer.created is True
    assert created.writer.opened_for_append is False
    assert opened.writer.created is False
    assert opened.writer.opened_for_append is True
    assert state.writer is None


@pytest.mark.parametrize("operation", ["create", "open_for_append"])
def test_lifecycle_validates_state_before_using_the_supplied_writer(
    behavior: LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
    state: LopSfFccVtkhdfAnimationWriterState,
    stub_writer: Any,
    operation: str,
) -> None:
    invalid = state.replace({"file_path": Path("invalid.h5")})

    with pytest.raises(DataWriterConfigurationError):
        getattr(behavior, operation)(invalid, stub_writer)

    assert not stub_writer.created
    assert not stub_writer.opened_for_append


def test_phase_two_modules_do_not_import_concrete_backends() -> None:
    module_paths = (
        Path(
            "src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer/"
            "lop_sf_fcc_vtkhdf_animation_writer_state.py"
        ),
        Path(
            "src/lammps_trajectory_analysis_tools/lib/lop_sf_fcc_vtkhdf_writer/"
            "lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior.py"
        ),
    )

    for module_path in module_paths:
        imported_modules = {
            alias.name
            for node in ast.walk(ast.parse(module_path.read_text()))
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module
            for node in ast.walk(ast.parse(module_path.read_text()))
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )

        assert "h5py" not in imported_modules
        assert all(not name.startswith("vtk") for name in imported_modules)
        assert all(
            not name.endswith("lop_sf_fcc_vtkhdf_animation_writer")
            for name in imported_modules
        )
