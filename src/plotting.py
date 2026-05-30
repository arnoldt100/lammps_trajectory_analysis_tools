"""
Visualization tools for trajectory analysis results.

Provides plotting functions for RDF, MSD, structure factor, and trajectory snapshots.
"""

from typing import Optional, Union
from pathlib import Path
import numpy as np

from .trajectory import Trajectory
from .analysis import RadialDistributionFunction, MeanSquareDisplacement


def plot_rdf(
    rdf_data: Union[RadialDistributionFunction, tuple],
    filename: Optional[Union[str, Path]] = None,
    **kwargs,
) -> None:
    """
    Plot radial distribution function.
    
    Args:
        rdf_data: RDF object or (r_values, g_r) tuple
        filename: Output file path (if None, display only)
        **kwargs: Additional matplotlib parameters
    """
    raise NotImplementedError()


def plot_msd(
    msd_data: Union[MeanSquareDisplacement, tuple],
    filename: Optional[Union[str, Path]] = None,
    **kwargs,
) -> None:
    """
    Plot mean square displacement vs time.
    
    Args:
        msd_data: MSD object or (times, msd_values) tuple
        filename: Output file path (if None, display only)
        **kwargs: Additional matplotlib parameters
    """
    raise NotImplementedError()


def plot_structure_factor(
    sq_data: tuple,
    filename: Optional[Union[str, Path]] = None,
    **kwargs,
) -> None:
    """
    Plot static structure factor S(q).
    
    Args:
        sq_data: (q_values, sq) tuple
        filename: Output file path (if None, display only)
        **kwargs: Additional matplotlib parameters
    """
    raise NotImplementedError()


def plot_trajectory(
    trajectory: Trajectory,
    frame_indices: Optional[list] = None,
    filename: Optional[Union[str, Path]] = None,
    animate: bool = False,
    **kwargs,
) -> None:
    """
    Visualize trajectory frames.
    
    Args:
        trajectory: Trajectory object
        frame_indices: Which frames to plot (default: all)
        filename: Output file path or animation file
        animate: If True, create animation; else plot grid of frames
        **kwargs: Additional visualization parameters
    """
    raise NotImplementedError()
