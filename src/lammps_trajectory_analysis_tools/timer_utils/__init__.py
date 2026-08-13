# Public API for the Timer package.

__all__ = []

# Register all timer classes with the GeneralTimerBu8ilder.
from .LoopTimerBuilder import ( LoopTimerBuilder,
                                LoopTimerBuilderKey )

from .GeneralTimerBuilder import GeneralTimerBuilder
timer_object_factory = GeneralTimerBuilder()
timer_object_factory.register_builder(LoopTimerBuilderKey ,LoopTimerBuilder)
