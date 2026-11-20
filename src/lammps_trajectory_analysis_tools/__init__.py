"""
LAMMPS Trajectory Analysis Tools

A Python package for parsing, analyzing, and visualizing LAMMPS molecular dynamics trajectories.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

def import_mdanalysis_with_affinity(env_var="MDA_RESTORE_AFFINITY"):
    import os

    """Import MDAnalysis while optionally preserving the original CPU affinity mask."""
    restore = os.environ.get(env_var, "").lower() in ("1", "true", "yes")
    can_manage_affinity = hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity")

    orig_affinity = None
    if restore and can_manage_affinity:
        orig_affinity = os.sched_getaffinity(0)

    import MDAnalysis

    if orig_affinity is not None:
        os.sched_setaffinity(0, orig_affinity)

    return MDAnalysis

MDAnalysis = import_mdanalysis_with_affinity()

from .trajectory import read_dump, Trajectory, TrajectoryReader, Frame
from .analysis import RadialDistributionFunction, MeanSquareDisplacement
from .plotting import plot_rdf, plot_trajectory

__all__ = [
    "MDAnalysis",
    "import_mdanalysis_with_affinity",
    "lib",
    "timer_utils",
    "parallelization",
    "read_dump",
    "Trajectory",
    "TrajectoryReader",
    "Frame",
    "RadialDistributionFunction",
    "MeanSquareDisplacement",
    "plot_rdf",
    "plot_trajectory",
]
