import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    BuilderKeyError,
    BuilderRegistry,
    BuilderRegistrationError,
    SupportsBuild,
)
from lammps_trajectory_analysis_tools.timer_utils import (
    LoopTimer,
    LoopTimerBuilder,
    LoopTimerBuilderKey,
    timer_object_factory,
)
from lammps_trajectory_analysis_tools.timer_utils.GeneralTimerBuilder import (
    GeneralTimerBuilder,
)


def test_loop_timer_builder_satisfies_builder_protocol() -> None:
    builder = LoopTimerBuilder()

    assert isinstance(builder, SupportsBuild)


def test_loop_timer_builder_forwards_constructor_arguments() -> None:
    timer = LoopTimerBuilder()(
        label="Builder",
        total_iterations=10,
        report_interval=2,
    )

    assert isinstance(timer, LoopTimer)
    assert timer.label == "Builder"
    assert timer.total == 10
    assert timer.interval == 2


def test_general_timer_builder_is_shared_registry_template() -> None:
    registry = GeneralTimerBuilder()

    registry.register_builder("loop", LoopTimerBuilder())

    timer = registry.build("loop", "Registered", 5, 1)

    assert isinstance(timer, LoopTimer)
    assert registry.keys() == frozenset({"loop"})


def test_timer_factory_has_one_registered_builder() -> None:
    assert timer_object_factory.keys() == frozenset({LoopTimerBuilderKey})

    timer = timer_object_factory.build(LoopTimerBuilderKey, "Factory", 5, 1)

    assert isinstance(timer, LoopTimer)


def test_timer_factory_rejects_unknown_builder_key() -> None:
    with pytest.raises(BuilderKeyError):
        timer_object_factory.build("missing", "Factory", 5, 1)


def test_builder_registry_rejects_duplicate_timer_key() -> None:
    registry: BuilderRegistry[LoopTimer] = BuilderRegistry()
    registry.register_builder(LoopTimerBuilderKey, LoopTimerBuilder())

    with pytest.raises(BuilderRegistrationError):
        registry.register_builder(LoopTimerBuilderKey, LoopTimerBuilder())
