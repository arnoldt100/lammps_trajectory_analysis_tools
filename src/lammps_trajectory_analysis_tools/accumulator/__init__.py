"""Accumulator data structures and merge helpers."""

from .accumulator_protocol import AccumulatorProtocol
from .array_accumulator import ArrayAccumulator
from .array_accumulator_builder import (
	ArrayAccumulatorBuilder,
	array_accumulator_builder_key,
)
from .merge_accumulators import merge_array_accumulators

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
	BuilderRegistry,
)

array_accumulator_builder_registry: BuilderRegistry[ArrayAccumulator] = BuilderRegistry()
array_accumulator_builder_registry.register_builder(
	array_accumulator_builder_key,
	ArrayAccumulatorBuilder(),
)

__all__ = [
	"AccumulatorProtocol",
	"ArrayAccumulator",
	"ArrayAccumulatorBuilder",
	"array_accumulator_builder_key",
	"array_accumulator_builder_registry",
	"merge_array_accumulators",
]