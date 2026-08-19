"""Public API for timer products and their builder registry."""

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    BuilderRegistry,
)

from .GeneralTimerBuilder import GeneralTimerBuilder
from .LoopTimer import LoopTimer
from .LoopTimerBuilder import LoopTimerBuilder, LoopTimerBuilderKey

timer_object_factory: BuilderRegistry[LoopTimer] = BuilderRegistry()
timer_object_factory.register_builder(LoopTimerBuilderKey, LoopTimerBuilder())

__all__ = [
    "GeneralTimerBuilder",
    "LoopTimer",
    "LoopTimerBuilder",
    "LoopTimerBuilderKey",
    "timer_object_factory",
]
