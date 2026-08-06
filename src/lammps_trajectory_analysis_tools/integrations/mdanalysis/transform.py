#! /usr/bin/env python3
"""Coordinate transformation helpers for MDAnalysis trajectories."""

from __future__ import annotations

import numpy as np

from lammps_trajectory_analysis_tools.lib.data_types import AtomCoordinates


def center_coordinates(coordinates: AtomCoordinates) -> AtomCoordinates:
    """Center coordinates around their centroid.

    Args:
        coordinates: Coordinate array with shape (n_atoms, 3).

    Returns:
        Centered coordinate array with shape (n_atoms, 3).
    """
    centroid = np.mean(coordinates, axis=0)
    return coordinates - centroid
