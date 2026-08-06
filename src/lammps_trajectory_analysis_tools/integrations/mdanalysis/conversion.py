#! /usr/bin/env python3
"""Conversion helpers from MDAnalysis objects to internal project arrays."""

from __future__ import annotations

import numpy as np
import MDAnalysis as mda

from lammps_trajectory_analysis_tools.lib.data_types import AtomCoordinates


def to_internal_trajectory(universe_mda: mda.Universe) -> AtomCoordinates:
    """Extract coordinates for the current frame as an internal array type.

    Args:
        universe_mda: MDAnalysis universe positioned at a trajectory frame.

    Returns:
        Coordinates with shape (n_atoms, 3) and dtype float64.
    """
    return np.asarray(universe_mda.atoms.positions, dtype=np.float64)
