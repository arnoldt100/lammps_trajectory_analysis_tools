#! /usr/bin/env python3
"""Concrete builders for the LOP SF FCC trajectory writer products.

This module provides the following public members:
    LopSfFccRunMetadataBuilder: Build run metadata values.
    LopSfFccTrajectoryLayoutBuilder: Build trajectory layout values.
    HDF5LopSfFccTrajectoryDataWriterBuilder: Build concrete data writers.
    HDF5LopSfFccTrajectoryWriterValueObjectBuilder: Build writer value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_lop_sf_fcc_trajectory_data_writer import (
    HDF5LopSfFccTrajectoryDataWriter,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_behavior import (
    LopSfFccTrajectoryWriterBehavior,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_builder_keys import (
    HDF5LopSfFccTrajectoryDataWriterBuilderKey,
    LopSfFccRunMetadataBuilderKey,
    LopSfFccTrajectoryLayoutBuilderKey,
)
from lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_value_object import (
    HDF5LopSfFccTrajectoryWriterValueObject,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)


# ----------
# Public members
# ----------
class LopSfFccRunMetadataBuilder:
    """Build ``LopSfFccRunMetadata`` values."""

    def __call__(self, *args: Any, **kwargs: Any) -> lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccRunMetadata:
        """Construct and return run metadata from the given arguments."""
        return lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccRunMetadata(*args, **kwargs)


class LopSfFccTrajectoryLayoutBuilder:
    """Build ``LopSfFccTrajectoryLayout`` values."""

    def __call__(self, *args: Any, **kwargs: Any) -> lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccTrajectoryLayout:
        """Construct and return a trajectory layout from the given arguments."""
        return lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccTrajectoryLayout(*args, **kwargs)


class HDF5LopSfFccTrajectoryDataWriterBuilder:
    """Build ``HDF5LopSfFccTrajectoryDataWriter`` instances."""

    def __call__(self, *args: Any, **kwargs: Any) -> HDF5LopSfFccTrajectoryDataWriter:
        """Construct and return a concrete data writer."""
        return HDF5LopSfFccTrajectoryDataWriter(*args, **kwargs)


class HDF5LopSfFccTrajectoryWriterValueObjectBuilder:
    """Build writer value objects, assembling their metadata and layout.

    The registry is injected rather than looked up globally, so the composite
    build path is substitutable in tests.
    """

    __slots__ = ("_registry",)

    def __init__(self, registry: BuilderRegistry[Any]) -> None:
        """Initialize the composite builder.

        Args:
            registry: Registry holding the metadata, layout, and writer
                builders.
        """
        self._registry = registry

    @property
    def registry(self) -> BuilderRegistry[Any]:
        """Return the registry used to build the composed products."""
        return self._registry

    def __call__(
        self,
        file_path: str | Path,
        metadata: lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccRunMetadata | Mapping[str, Any],
        layout: lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccTrajectoryLayout | Mapping[str, Any],
    ) -> HDF5LopSfFccTrajectoryWriterValueObject:
        """Build a writer value object that owns no writer yet.

        Args:
            file_path: Path of the HDF5 output target.
            metadata: Run metadata, or a mapping of its constructor arguments.
            layout: Trajectory layout, or a mapping of its constructor
                arguments.
        """
        built_metadata = self._resolve(
            metadata,
            lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccRunMetadata,
            LopSfFccRunMetadataBuilderKey,
        )
        built_layout = self._resolve(
            layout,
            lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccTrajectoryLayout,
            LopSfFccTrajectoryLayoutBuilderKey,
        )
        state = lammps_trajectory_analysis_tools.data_writer_utils.lop_sf_fcc_trajectory_writer_state.LopSfFccTrajectoryWriterState(file_path, built_metadata, built_layout)
        behavior = LopSfFccTrajectoryWriterBehavior(
            self._registry,
            HDF5LopSfFccTrajectoryDataWriterBuilderKey,
        )
        return HDF5LopSfFccTrajectoryWriterValueObject(state, behavior)

    def _resolve(self, value: Any, product_type: type, key: str) -> Any:
        if isinstance(value, product_type):
            return value
        return self._registry.build(key, **dict(value))

# ----------
# Private members
# ----------

def _main() -> None:
    return


if __name__ == "__main__":
    _main()
