#! /usr/bin/env python3
"""Thin bridge functions wiring MDAnalysis inputs to project analyses."""

from __future__ import annotations

import numpy as np
import MDAnalysis as mda

from lammps_trajectory_analysis_tools.integrations.mdanalysis.conversion import to_internal_trajectory
from lammps_trajectory_analysis_tools.integrations.mdanalysis.errors import (
    AnalysisBridgeExecutionError,
    BridgeValidationError,
)
from lammps_trajectory_analysis_tools.lib.data_types import (
    AtomCoordinates,
    AtomExpAccumTerm,
    LatticeVectors,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc import (
    calculate_sf_fcc_atom_order_parameter_no_coeffs,
)


def run_lop_sf_fcc_from_universe(universe_mda: mda.Universe) -> AtomCoordinates:
    """Return converted coordinates used by downstream LOP/SF FCC routines.

    Args:
        universe_mda: MDAnalysis universe at the frame to analyze.

    Returns:
        Project-internal coordinates for the selected frame.
    """
    _validate_universe(universe_mda)
    coordinates = to_internal_trajectory(universe_mda)
    return np.asarray(coordinates, dtype=np.float64)


def run_lop_sf_fcc_terms_from_universe(
    universe_mda: mda.Universe,
    wave_vectors: LatticeVectors,
    cutoff: float,
) -> AtomExpAccumTerm:
    """Run the core no-coefficient LOP/SF FCC analysis from an MDAnalysis universe.

    Args:
        universe_mda: MDAnalysis universe positioned at the analysis frame.
        wave_vectors: Wave-vector array with shape ``(N, 3)``.
        cutoff: Neighbor-search cutoff in angstroms.

    Returns:
        Complex accumulation terms for each atom.

    Raises:
        BridgeValidationError: If analysis inputs fail validation.
        AnalysisBridgeExecutionError: If delegated core analysis fails.
    """
    _validate_universe(universe_mda)
    _validate_wave_vectors(wave_vectors)
    _validate_cutoff(cutoff)

    try:
        terms = calculate_sf_fcc_atom_order_parameter_no_coeffs(
            universe_mda,
            np.asarray(wave_vectors, dtype=np.float64),
            float(cutoff),
        )
    except Exception as exc:  # pragma: no cover - passthrough wrapper
        raise AnalysisBridgeExecutionError(str(exc)) from exc

    return np.asarray(terms, dtype=np.complex64)


def _validate_universe(universe_mda: mda.Universe) -> None:
    """Validate that a universe contains atoms and simulation dimensions."""
    if universe_mda is None:
        raise BridgeValidationError("universe_mda must not be None")

    if universe_mda.atoms.n_atoms <= 0:
        raise BridgeValidationError("universe_mda must contain at least one atom")

    if universe_mda.dimensions is None:
        raise BridgeValidationError("universe_mda must define simulation box dimensions")

    if len(universe_mda.dimensions) != 6:
        raise BridgeValidationError("universe_mda.dimensions must have length 6")


def _validate_wave_vectors(wave_vectors: LatticeVectors) -> None:
    """Validate wave-vector shape required by core LOP/SF FCC analysis."""
    wave_vector_array = np.asarray(wave_vectors)

    if wave_vector_array.ndim != 2:
        raise BridgeValidationError("wave_vectors must be a 2D array")

    if wave_vector_array.shape[0] <= 0:
        raise BridgeValidationError("wave_vectors must contain at least one vector")

    if wave_vector_array.shape[1] != 3:
        raise BridgeValidationError("wave_vectors must have shape (N, 3)")


def _validate_cutoff(cutoff: float) -> None:
    """Validate neighbor-search cutoff used by core LOP/SF FCC analysis."""
    if cutoff <= 0.0:
        raise BridgeValidationError("cutoff must be greater than zero")
