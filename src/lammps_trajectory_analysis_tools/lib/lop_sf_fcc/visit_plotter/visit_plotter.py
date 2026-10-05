#! /usr/bin/env python3
"""Orchestrating plotter for the LOP SF FCC VisIt time series.

This module provides the following public members:
    LopSfFccVisitPlotter: Export a master ``.xdmf`` and render it headlessly.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.lop_sf_fcc_series_exporter import (
    LopSfFccXdmfExporter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.plotter_exceptions import (
    PlotterConfigurationError,
    PlotterRenderError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_installation import (
    VisitInstallation,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_render_script import (
    render_script_text,
)

# ----------
# Public members
# ----------


class LopSfFccVisitPlotter:
    """Render a LOP SF FCC HDF5 file as a headless VisIt time series.

    The plotter exports a master ``.xdmf`` temporal collection and then runs
    VisIt's CLI as a subprocess (``-cli -nowin``) in a scrubbed environment
    (no ``PYTHON_GIL``; extra library dirs prepended). VisIt is never imported
    in-process.
    """

    __slots__ = ("_installation", "_timeout")

    def __init__(
        self,
        installation: VisitInstallation,
        timeout: float = 300.0,
    ) -> None:
        """Initialize the plotter.

        Args:
            installation: The located, validated VisIt installation.
            timeout: Seconds to wait for the render subprocess.

        Raises:
            PlotterConfigurationError: If ``timeout`` is not positive.
        """
        if timeout <= 0:
            raise PlotterConfigurationError(
                f"timeout must be positive, got {timeout!r}"
            )
        self._installation = installation
        self._timeout = float(timeout)

    @property
    def installation(self) -> VisitInstallation:
        """Return the VisIt installation used for rendering."""
        return self._installation

    @property
    def timeout(self) -> float:
        """Return the render subprocess timeout in seconds."""
        return self._timeout

    def export_xdmf(
        self,
        source_path: str | Path,
        output_path: str | Path,
    ) -> Path:
        """Export the master ``.xdmf`` for a source HDF5 file.

        Args:
            source_path: The LOP SF FCC HDF5 file.
            output_path: Destination ``.xdmf`` path.

        Returns:
            The written ``.xdmf`` path.
        """
        exporter = LopSfFccXdmfExporter(source_path)
        return exporter.export(output_path)

    def render(
        self,
        source_path: str | Path,
        output_dir: str | Path,
        color_min: float = 0.0,
        color_max: float = 1.0,
    ) -> list[Path]:
        """Export and render the time series, returning the written PNGs.

        Args:
            source_path: The LOP SF FCC HDF5 file.
            output_dir: Directory for the per-frame PNGs.
            color_min: Global pseudocolor minimum (fixed across frames).
            color_max: Global pseudocolor maximum (fixed across frames).

        Returns:
            The sorted list of written PNG paths.

        Raises:
            PlotterConfigurationError: If the color range is invalid.
            PlotterRenderError: If the VisIt subprocess fails to render.
        """
        if not color_max > color_min:
            raise PlotterConfigurationError(
                f"color_max ({color_max!r}) must exceed color_min "
                f"({color_min!r})"
            )

        output_directory = Path(output_dir)
        output_directory.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ltat_visit_plot_") as scratch:
            scratch_dir = Path(scratch)
            master_xdmf = self.export_xdmf(
                source_path, scratch_dir / "lop_sf_fcc_time_series.xdmf"
            )
            script_path = scratch_dir / "render.py"
            script_path.write_text(render_script_text(), encoding="utf-8")
            self._run_visit(master_xdmf, output_directory, color_min, color_max)

        frames = sorted(output_directory.glob("frame_*.png"))
        if not frames:
            raise PlotterRenderError(
                f"VisIt produced no frames in '{output_directory}'"
            )
        return frames

    def _run_visit(
        self,
        master_xdmf: Path,
        output_dir: Path,
        color_min: float,
        color_max: float,
    ) -> None:
        """Run the headless VisIt render subprocess."""
        command = [
            str(self._installation.launcher),
            "-cli",
            "-nowin",
            "-s",
            str(master_xdmf.parent / "render.py"),
            str(master_xdmf),
            str(output_dir),
            repr(color_min),
            repr(color_max),
        ]
        env = self._installation.subprocess_environment()
        try:
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise PlotterRenderError(
                f"VisIt render timed out after {self._timeout} s"
            ) from error
        except OSError as error:
            raise PlotterRenderError(
                f"could not launch VisIt '{command[0]}'"
            ) from error

        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0 or "RENDER_OK" not in result.stdout:
            raise PlotterRenderError(
                f"VisIt render failed (exit {result.returncode}): "
                f"{output.strip()!r}"
            )


# ----------
# Private members
# ----------


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
