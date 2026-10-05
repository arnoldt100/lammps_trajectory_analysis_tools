#! /usr/bin/env python3
"""Concrete builders for the LOP SF FCC VisIt plotter products.

This module provides the following public members:
    VisitInstallationBuilder: Build validated ``VisitInstallation`` values.
    LopSfFccVisitPlotterBuilder: Build ``LopSfFccVisitPlotter`` instances.
"""

from __future__ import annotations

from typing import Any

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_installation import (
    VisitInstallation,
    locate_visit_installation,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_plotter import (
    LopSfFccVisitPlotter,
)

# ----------
# Public members
# ----------


class VisitInstallationBuilder:
    """Build ``VisitInstallation`` values by locating the VisIt launcher."""

    def __call__(self, *args: Any, **kwargs: Any) -> VisitInstallation:
        """Locate and return a validated VisIt installation.

        Accepts the same arguments as ``locate_visit_installation``.
        """
        return locate_visit_installation(*args, **kwargs)


class LopSfFccVisitPlotterBuilder:
    """Build ``LopSfFccVisitPlotter`` instances."""

    def __call__(self, *args: Any, **kwargs: Any) -> LopSfFccVisitPlotter:
        """Construct and return a plotter."""
        return LopSfFccVisitPlotter(*args, **kwargs)


# ----------
# Private members
# ----------


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
