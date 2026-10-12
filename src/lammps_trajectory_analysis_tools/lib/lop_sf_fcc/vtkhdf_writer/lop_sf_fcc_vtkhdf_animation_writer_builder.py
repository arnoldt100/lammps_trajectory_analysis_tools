"""Concrete builders for LOP SF FCC VTKHDF animation writer products.

This module is the feature's single owner of concrete builders.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
    BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer import (
    LopSfFccVtkhdfAnimationWriter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_builder_keys import (
    LopSfFccVtkhdfAnimationLayoutBuilderKey,
    LopSfFccVtkhdfAnimationMetadataBuilderKey,
    LopSfFccVtkhdfAnimationWriterBuilderKey,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_state import (
    LopSfFccVtkhdfAnimationLayout,
    LopSfFccVtkhdfAnimationMetadata,
    LopSfFccVtkhdfAnimationWriterState,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object import (
    LopSfFccVtkhdfAnimationWriterValueObject,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.vtkhdf_writer.lop_sf_fcc_vtkhdf_animation_writer_value_object_behavior import (
    LopSfFccVtkhdfAnimationWriterValueObjectBehavior,
)


# ----------
# Public members
# ----------
class LopSfFccVtkhdfAnimationMetadataBuilder:
    """Build immutable VTKHDF animation metadata."""

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> LopSfFccVtkhdfAnimationMetadata:
        """Construct and return animation metadata."""
        return LopSfFccVtkhdfAnimationMetadata(*args, **kwargs)


class LopSfFccVtkhdfAnimationLayoutBuilder:
    """Build immutable VTKHDF animation layouts."""

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> LopSfFccVtkhdfAnimationLayout:
        """Construct and return an animation layout."""
        return LopSfFccVtkhdfAnimationLayout(*args, **kwargs)


class LopSfFccVtkhdfAnimationWriterBuilder:
    """Build concrete VTKHDF animation writers."""

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> LopSfFccVtkhdfAnimationWriter:
        """Construct and return a concrete animation writer."""
        return LopSfFccVtkhdfAnimationWriter(*args, **kwargs)


class LopSfFccVtkhdfAnimationWriterValueObjectBuilder:
    """Build composite VTKHDF animation writer value objects."""

    __slots__ = ("_registry",)

    def __init__(self, registry: BuilderRegistry[Any]) -> None:
        """Initialize with the feature registry.

        Args:
            registry: Registry holding metadata, layout, and writer builders.
        """
        self._registry = registry

    def __call__(
        self,
        file_path: str | Path,
        metadata: LopSfFccVtkhdfAnimationMetadata | Mapping[str, Any],
        layout: LopSfFccVtkhdfAnimationLayout | Mapping[str, Any],
    ) -> LopSfFccVtkhdfAnimationWriterValueObject:
        """Build a closed animation writer value object.

        Args:
            file_path: Final VTKHDF target path.
            metadata: Metadata value or its constructor arguments.
            layout: Layout value or its constructor arguments.
        """
        built_metadata = self._resolve_metadata(metadata)
        built_layout = self._resolve_layout(layout)
        state = LopSfFccVtkhdfAnimationWriterState(
            file_path,
            built_metadata,
            built_layout,
        )
        behavior = LopSfFccVtkhdfAnimationWriterValueObjectBehavior(
            self._registry,
            LopSfFccVtkhdfAnimationWriterBuilderKey,
        )
        return LopSfFccVtkhdfAnimationWriterValueObject(state, behavior)

    def _resolve_metadata(
        self,
        value: LopSfFccVtkhdfAnimationMetadata | Mapping[str, Any],
    ) -> LopSfFccVtkhdfAnimationMetadata:
        if isinstance(value, LopSfFccVtkhdfAnimationMetadata):
            return value
        return self._registry.build(
            LopSfFccVtkhdfAnimationMetadataBuilderKey,
            **dict(value),
        )

    def _resolve_layout(
        self,
        value: LopSfFccVtkhdfAnimationLayout | Mapping[str, Any],
    ) -> LopSfFccVtkhdfAnimationLayout:
        if isinstance(value, LopSfFccVtkhdfAnimationLayout):
            return value
        return self._registry.build(
            LopSfFccVtkhdfAnimationLayoutBuilderKey,
            **dict(value),
        )


# ----------
# Private members
# ----------
def _main() -> None:
    return


if __name__ == "__main__":
    _main()
