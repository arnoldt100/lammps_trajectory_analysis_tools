import inspect

import pytest

from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object_interface import (
    LopSfFccTrajectoryWriterValueObjectInterface,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.value_object_interface import (
    ValueObjectInterface,
)

EXPECTED_ABSTRACT_MEMBERS = frozenset(
    {
        "state_implementations",
        "metadata",
        "writer_configuration",
        "replace",
        "dummy_method",
        "create",
        "append_trajectory_frames",
        "close",
        "__enter__",
        "__exit__",
        "__eq__",
        "__repr__",
    }
)


def test_interface_extends_the_value_object_template() -> None:
    assert issubclass(LopSfFccTrajectoryWriterValueObjectInterface, ValueObjectInterface)


def test_interface_stores_no_instance_data() -> None:
    assert LopSfFccTrajectoryWriterValueObjectInterface.__slots__ == ()


def test_interface_declares_every_documented_abstract_member() -> None:
    assert (
        LopSfFccTrajectoryWriterValueObjectInterface.__abstractmethods__
        == EXPECTED_ABSTRACT_MEMBERS
    )


def test_interface_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        LopSfFccTrajectoryWriterValueObjectInterface()  # type: ignore[abstract]


def test_incomplete_implementation_cannot_be_instantiated() -> None:
    class _Incomplete(LopSfFccTrajectoryWriterValueObjectInterface):
        __slots__ = ()

        def create(self) -> None:
            return None

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_complete_implementation_can_be_instantiated() -> None:
    implementation = _minimal_implementation()

    assert isinstance(implementation, LopSfFccTrajectoryWriterValueObjectInterface)


def test_append_trajectory_frames_declares_the_documented_parameters() -> None:
    signature = inspect.signature(
        LopSfFccTrajectoryWriterValueObjectInterface.append_trajectory_frames
    )

    assert list(signature.parameters) == [
        "self",
        "trajectory_index",
        "step_numbers",
        "positions",
        "lop_sf_fcc_values",
        "box_lengths",
        "box_angles",
    ]


def _minimal_implementation() -> LopSfFccTrajectoryWriterValueObjectInterface:
    class _Minimal(LopSfFccTrajectoryWriterValueObjectInterface):
        __slots__ = ()

        @property
        def state_implementations(self):
            return None

        @property
        def metadata(self):
            return {}

        @property
        def writer_configuration(self):
            return {}

        def replace(self, changes):
            return self

        def dummy_method(self):
            return None

        def create(self) -> None:
            return None

        def append_trajectory_frames(
            self,
            trajectory_index,
            step_numbers,
            positions,
            lop_sf_fcc_values,
            box_lengths,
            box_angles,
        ) -> None:
            return None

        def close(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception, traceback) -> None:
            return None

        def __eq__(self, other: object) -> bool:
            return self is other

        def __repr__(self) -> str:
            return "_Minimal()"

    return _Minimal()
