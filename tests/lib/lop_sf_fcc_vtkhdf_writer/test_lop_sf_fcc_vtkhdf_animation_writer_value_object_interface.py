"""Tests for the VTKHDF animation writer value-object interface."""

import inspect

import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.value_object_interface import (
    ValueObjectInterface,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_interface import (
    LopSfFccVtkhdfAnimationWriterValueObjectInterface,
)

EXPECTED_ABSTRACT_MEMBERS = frozenset(
    {
        "state_implementations",
        "metadata",
        "writer_configuration",
        "replace",
        "update",
        "dummy_method",
        "create",
        "open_for_append",
        "append_frames",
        "close",
        "abort",
        "__enter__",
        "__exit__",
        "__eq__",
        "__repr__",
    }
)


def test_interface_extends_the_value_object_template() -> None:
    assert issubclass(
        LopSfFccVtkhdfAnimationWriterValueObjectInterface,
        ValueObjectInterface,
    )


def test_interface_stores_no_instance_data() -> None:
    assert LopSfFccVtkhdfAnimationWriterValueObjectInterface.__slots__ == ()


def test_interface_declares_the_complete_contract() -> None:
    assert (
        LopSfFccVtkhdfAnimationWriterValueObjectInterface.__abstractmethods__
        == EXPECTED_ABSTRACT_MEMBERS
    )


def test_interface_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        LopSfFccVtkhdfAnimationWriterValueObjectInterface()  # type: ignore[abstract]


def test_append_frames_declares_the_documented_parameters() -> None:
    signature = inspect.signature(
        LopSfFccVtkhdfAnimationWriterValueObjectInterface.append_frames
    )

    assert list(signature.parameters) == [
        "self",
        "step_numbers",
        "positions",
        "lop_sf_fcc_values",
        "box_lengths",
        "box_angles",
    ]
