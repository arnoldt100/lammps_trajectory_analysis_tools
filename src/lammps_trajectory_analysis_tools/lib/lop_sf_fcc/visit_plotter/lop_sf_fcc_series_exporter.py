#! /usr/bin/env python3
"""Export a LOP SF FCC HDF5 file to a master Xdmf time series.

This module provides the following public members:
    LopSfFccXdmfExporter: Write a master ``.xdmf`` file that VisIt can sweep
        over time, referencing the source HDF5 datasets in place.
    SPATIAL_DIMENSION: The fixed spatial dimension of every simulation.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import h5py
import numpy as np

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.plotter_exceptions import (
    PlotterConfigurationError,
)

# ----------
# Public members
# ----------

"""The fixed spatial dimension of every simulation (all runs are 3-D)."""
SPATIAL_DIMENSION = 3

_TRAJECTORY_ROOT = "trajectories"
_POSITIONS = "positions"
_LOP_SF_FCC = "lop_sf_fcc"
_STEP_NUMBER = "step_number"
_LOP_ATTRIBUTE_NAME = "lop_sf_fcc"


class LopSfFccXdmfExporter:
    """Write a master ``.xdmf`` temporal collection for a LOP SF FCC HDF5 file.

    Each ``traj_NNNNN`` group becomes one timestep in a single temporal
    collection grid. Heavy data (``positions`` and ``lop_sf_fcc``) is
    referenced in place via HDF5 ``DataItem`` hyperlinks, so the master file
    is a small text index with no data duplication.
    """

    __slots__ = ("_source_path",)

    def __init__(self, source_path: str | Path) -> None:
        """Initialize the exporter for one source HDF5 file.

        Args:
            source_path: Path to the LOP SF FCC HDF5 file.

        Raises:
            PlotterConfigurationError: If the file is missing or not HDF5.
        """
        path = Path(source_path)
        if not path.is_file():
            raise PlotterConfigurationError(
                f"source HDF5 file not found: '{path}'"
            )
        if not h5py.is_hdf5(path):
            raise PlotterConfigurationError(
                f"source file is not HDF5: '{path}'"
            )
        self._source_path = path

    @property
    def source_path(self) -> Path:
        """Return the source HDF5 file path."""
        return self._source_path

    def export(self, output_path: str | Path) -> Path:
        """Write the master ``.xdmf`` file and return its path.

        Args:
            output_path: Destination ``.xdmf`` path. HDF5 references are
                written as absolute paths so the ``.xdmf`` can live anywhere
                (for example in a render scratch directory) regardless of
                where the source HDF5 file is.

        Returns:
            The written ``.xdmf`` path.

        Raises:
            PlotterConfigurationError: If the source layout is invalid.
        """
        output = Path(output_path)
        with h5py.File(self._source_path, "r") as handle:
            time_step = _read_time_step(handle)
            frames = _collect_frames(handle)

        hdf_ref = self._source_path.resolve().as_posix()
        document = self._build_document(frames, time_step, hdf_ref)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
        return output

    def _build_document(
        self,
        frames: list["_FrameRef"],
        time_step: float,
        hdf_ref: str,
    ) -> str:
        """Build the master Xdmf XML document text."""
        lines = [
            '<?xml version="1.0" ?>',
            '<!DOCTYPE Xdmf SYSTEM "Xdmf.dtd">',
            '<Xdmf Version="3.0">',
            "  <Domain>",
            '    <Grid Name="lop_sf_fcc_time_series" GridType="Collection"'
            ' CollectionType="Temporal">',
        ]
        for frame in frames:
            time_value = frame.step_number * time_step
            lines.extend(
                [
                    f'      <Grid Name="{escape(frame.name)}" GridType="Uniform">',
                    f'        <Time Value="{time_value!r}"/>',
                    f'        <Topology TopologyType="PolyVertex"'
                    f' NumberOfElements="{frame.number_of_atoms}"/>',
                    '        <Geometry GeometryType="XYZ">',
                    _data_item(
                        frame.number_of_atoms,
                        SPATIAL_DIMENSION,
                        frame.positions_precision,
                        hdf_ref,
                        frame.positions_path,
                        indent=10,
                    ),
                    "        </Geometry>",
                    f'        <Attribute Name="{_LOP_ATTRIBUTE_NAME}"'
                    ' AttributeType="Scalar" Center="Node">',
                    _data_item(
                        frame.number_of_atoms,
                        None,
                        frame.lop_precision,
                        hdf_ref,
                        frame.lop_path,
                        indent=10,
                    ),
                    "        </Attribute>",
                    "      </Grid>",
                ]
            )
        lines.extend(["    </Grid>", "  </Domain>", "</Xdmf>", ""])
        return "\n".join(lines)


# ----------
# Private members
# ----------


class _FrameRef:
    """One timestep's dataset references and shapes."""

    __slots__ = (
        "lop_path",
        "lop_precision",
        "name",
        "number_of_atoms",
        "positions_path",
        "positions_precision",
        "step_number",
    )

    def __init__(
        self,
        name: str,
        step_number: int,
        number_of_atoms: int,
        positions_path: str,
        positions_precision: int,
        lop_path: str,
        lop_precision: int,
    ) -> None:
        self.name = name
        self.step_number = step_number
        self.number_of_atoms = number_of_atoms
        self.positions_path = positions_path
        self.positions_precision = positions_precision
        self.lop_path = lop_path
        self.lop_precision = lop_precision


def _read_time_step(handle: "h5py.File") -> float:
    """Read the run ``time_step`` root attribute."""
    if "time_step" not in handle.attrs:
        raise PlotterConfigurationError(
            "source HDF5 file has no 'time_step' root attribute"
        )
    return float(handle.attrs["time_step"])


def _collect_frames(handle: "h5py.File") -> list[_FrameRef]:
    """Collect one frame reference per trajectory group, in index order."""
    if _TRAJECTORY_ROOT not in handle:
        raise PlotterConfigurationError(
            f"source HDF5 file has no '{_TRAJECTORY_ROOT}' group"
        )
    root = handle[_TRAJECTORY_ROOT]
    names = sorted(root.keys())
    if not names:
        raise PlotterConfigurationError(
            f"source HDF5 file has no trajectory groups under "
            f"'{_TRAJECTORY_ROOT}'"
        )

    frames: list[_FrameRef] = []
    for name in names:
        group = root[name]
        frame = _frame_from_group(name, group)
        if frame is not None:
            frames.append(frame)
    if not frames:
        raise PlotterConfigurationError(
            "no trajectory group holds any frames (all are empty)"
        )
    return frames


def _frame_from_group(name: str, group: "h5py.Group") -> _FrameRef | None:
    """Build a frame reference from one trajectory group, or ``None``.

    A group with zero stored frames (empty datasets) is skipped: it
    contributes no timestep.
    """
    for dataset in (_POSITIONS, _LOP_SF_FCC, _STEP_NUMBER):
        if dataset not in group:
            raise PlotterConfigurationError(
                f"trajectory group '{name}' is missing dataset '{dataset}'"
            )

    positions = group[_POSITIONS]
    lop = group[_LOP_SF_FCC]
    steps = group[_STEP_NUMBER]

    n_frames = positions.shape[0]
    if n_frames == 0:
        return None
    if n_frames > 1:
        raise PlotterConfigurationError(
            f"trajectory group '{name}' holds {n_frames} frames; the time "
            "mapping expects exactly one analysed frame per trajectory group"
        )
    if positions.ndim != 3 or positions.shape[2] != SPATIAL_DIMENSION:
        raise PlotterConfigurationError(
            f"'{name}/{_POSITIONS}' must have shape (n_frames, n_atoms, "
            f"{SPATIAL_DIMENSION}); got {positions.shape}"
        )
    n_atoms = positions.shape[1]
    if lop.shape != (n_frames, n_atoms):
        raise PlotterConfigurationError(
            f"'{name}/{_LOP_SF_FCC}' must have shape ({n_frames}, {n_atoms}); "
            f"got {lop.shape}"
        )
    if steps.shape != (n_frames,):
        raise PlotterConfigurationError(
            f"'{name}/{_STEP_NUMBER}' must have shape ({n_frames},); "
            f"got {steps.shape}"
        )

    # The plotter's time mapping treats each trajectory group as one timestep
    # (one analysed frame per group in the current writer). Use frame 0.
    return _FrameRef(
        name=name,
        step_number=int(steps[0]),
        number_of_atoms=int(n_atoms),
        positions_path=positions.name,
        positions_precision=_precision_bytes(positions.dtype, f"{name}/{_POSITIONS}"),
        lop_path=lop.name,
        lop_precision=_precision_bytes(lop.dtype, f"{name}/{_LOP_SF_FCC}"),
    )


def _precision_bytes(dtype: "np.dtype", dataset: str) -> int:
    """Return the Xdmf float precision (bytes) for a floating dataset."""
    np_dtype = np.dtype(dtype)
    if np_dtype.kind != "f":
        raise PlotterConfigurationError(
            f"dataset '{dataset}' must be floating-point; got {np_dtype}"
        )
    return int(np_dtype.itemsize)


def _data_item(
    count: int,
    width: int | None,
    precision: int,
    hdf_ref: str,
    dataset_path: str,
    indent: int,
) -> str:
    """Return one HDF5 ``DataItem`` XML line referencing a dataset in place."""
    dimensions = f"{count} {width}" if width is not None else f"{count}"
    pad = " " * indent
    reference = f"{hdf_ref}:{dataset_path}"
    return (
        f'{pad}<DataItem Format="HDF" DataType="Float" '
        f'Precision="{precision}" Dimensions="{dimensions}">'
        f"{escape(reference)}</DataItem>"
    )


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
