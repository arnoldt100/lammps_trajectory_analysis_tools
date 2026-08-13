"""
LAMMPS Trajectory Analysis Tools

A Python package for parsing, analyzing, and visualizing LAMMPS molecular dynamics trajectories.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Public API
from .trajectory import read_dump, Trajectory, TrajectoryReader, Frame
from .analysis import RadialDistributionFunction, MeanSquareDisplacement
from .plotting import plot_rdf, plot_trajectory

__all__ = [
    "lib",
    "timer_utils",
    "read_dump",
    "Trajectory",
    "TrajectoryReader",
    "Frame",
    "RadialDistributionFunction",
    "MeanSquareDisplacement",
    "plot_rdf",
    "plot_trajectory",
]
