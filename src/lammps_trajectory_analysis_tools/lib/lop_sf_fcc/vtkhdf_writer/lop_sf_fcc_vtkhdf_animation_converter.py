"""End-to-end conversion of LOP SF FCC sources to VTKHDF animations.

This module provides the following public members:
    LopSfFccVtkhdfAnimationConverter: Convert validated sources through the
        feature builder registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
)
from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_source_interface import (
    LopSfFccVtkhdfAnimationSourceInterface,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_builder_keys import (
    HDF5LopSfFccAnimationSourceBuilderKey,
    LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationLayout,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationConverter:
    """Convert validated animation sources through an injected registry."""

    __slots__ = ("_registry",)

    def __init__(self, registry: BuilderRegistry[Any]) -> None:
        """Initialize with the feature builder registry.

        Args:
            registry: Registry containing source and writer builders.
        """
        self._registry = registry

    def convert(
        self,
        source: LopSfFccVtkhdfAnimationSourceInterface,
        target_path: str | Path,
        *,
        layout: LopSfFccVtkhdfAnimationLayout | None = None,
    ) -> Path:
        """Convert an animation source to one VTKHDF target.

        Args:
            source: Closed animation source to validate and decode.
            target_path: Final ``.vtkhdf`` output path.
            layout: Optional output storage and dtype configuration. The source
                layout is used by default.

        Returns:
            The final target path.

        Raises:
            DataWriterConfigurationError: If an override changes atom count.
        """
        target = Path(target_path)
        with source:
            source_layout = source.layout
            output_layout = source_layout if layout is None else layout
            if output_layout.number_of_atoms != source_layout.number_of_atoms:
                raise DataWriterConfigurationError(
                    "output layout number_of_atoms must match the source"
                )
            writer = self._registry.build(
                LopSfFccVtkhdfAnimationWriterValueObjectBuilderKey,
                file_path=target,
                metadata=source.metadata,
                layout=output_layout,
            )
            with writer:
                for frame in source.frames():
                    writer.append_frames(
                        frame.step_number,
                        frame.positions,
                        frame.lop_sf_fcc_values,
                        frame.box_lengths,
                        frame.box_angles,
                    )
        return target

    def convert_hdf5(
        self,
        source_path: str | Path,
        target_path: str | Path,
        *,
        layout: LopSfFccVtkhdfAnimationLayout | None = None,
    ) -> Path:
        """Convert one producer HDF5 file to a VTKHDF animation.

        Args:
            source_path: Persisted LOP SF FCC HDF5 source.
            target_path: Final ``.vtkhdf`` output path.
            layout: Optional output storage and dtype configuration.

        Returns:
            The final target path.
        """
        source = self._registry.build(
            HDF5LopSfFccAnimationSourceBuilderKey,
            file_path=source_path,
        )
        return self.convert(source, target_path, layout=layout)


# ----------
# Private members
# ----------
def _main() -> None:
    return


if __name__ == "__main__":
    _main()
