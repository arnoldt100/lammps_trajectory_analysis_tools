"""Accumulator data structures and merge helpers."""

from .accumulator_protocol import AccumulatorProtocol
from lammps_trajectory_analysis_tools.accumulator.accumulator_value_protocol import (
	AccumulatorValueProtocol,
)
from .array_accumulator_value import ArrayAccumulatorValue
from lammps_trajectory_analysis_tools.accumulator.array_accumulator_value_state import (
	ArrayAccumulatorValueState,
)
from .array_accumulator_behavior import (
	ArrayAccumulatorBehavior,
	ArrayAccumulatorBehaviorProtocol,
	merge_accumulator_values,
	merge_array_accumulators,
)
from .array_accumulator_state import ArrayAccumulatorState
from .array_accumulator import ArrayAccumulator
from .array_accumulator_builder import (
	ArrayAccumulatorBuilder,
	array_accumulator_builder_key,
)
from lammps_trajectory_analysis_tools.accumulator.array_accumulator_value_builder import (
	ArrayAccumulatorValueBuilder,
	array_accumulator_value_builder_key,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
	BuilderRegistry,
)

array_accumulator_builder_registry: BuilderRegistry[ArrayAccumulator] = BuilderRegistry()
array_accumulator_builder_registry.register_builder(
	array_accumulator_builder_key,
	ArrayAccumulatorBuilder(),
)
array_accumulator_value_builder_registry: BuilderRegistry[ArrayAccumulatorValue] = (
	BuilderRegistry()
)
array_accumulator_value_builder_registry.register_builder(
	array_accumulator_value_builder_key,
	ArrayAccumulatorValueBuilder(),
)

__all__ = [
	"AccumulatorProtocol",
	"AccumulatorValueProtocol",
	"ArrayAccumulator",
	"ArrayAccumulatorBehavior",
	"ArrayAccumulatorBehaviorProtocol",
	"ArrayAccumulatorState",
	"ArrayAccumulatorValue",
	"ArrayAccumulatorValueState",
	"ArrayAccumulatorBuilder",
	"array_accumulator_builder_key",
	"array_accumulator_builder_registry",
	"ArrayAccumulatorValueBuilder",
	"array_accumulator_value_builder_key",
	"array_accumulator_value_builder_registry",
	"merge_array_accumulators",
	"merge_accumulator_values",
]