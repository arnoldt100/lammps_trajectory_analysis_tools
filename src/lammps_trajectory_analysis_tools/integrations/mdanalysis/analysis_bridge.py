#! /usr/bin/env python3
"""Thin bridge functions wiring MDAnalysis inputs to project analyses."""

from __future__ import annotations

import numpy as np
import MDAnalysis as mda

from lammps_trajectory_analysis_tools.integrations.mdanalysis.conversion import to_internal_trajectory
from lammps_trajectory_analysis_tools.lib.data_types import AtomCoordinates


def run_lop_sf_fcc_from_universe(universe_mda: mda.Universe) -> AtomCoordinates:
    """Return converted coordinates used by downstream LOP/SF FCC routines.

    Args:
        universe_mda: MDAnalysis universe at the frame to analyze.

    Returns:
        Project-internal coordinates for the selected frame.
    """
    coordinates = to_internal_trajectory(universe_mda)
    return np.asarray(coordinates, dtype=np.float64)
