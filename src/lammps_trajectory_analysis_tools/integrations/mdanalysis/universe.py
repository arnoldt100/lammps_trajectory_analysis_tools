#! /usr/bin/env python3
"""Universe loader helpers for MDAnalysis-backed workflows."""

from __future__ import annotations

from typing import Any

import MDAnalysis as mda
import numpy as np
from MDAnalysis.lib.pkdtree import PeriodicKDTree

from lammps_trajectory_analysis_tools.integrations.mdanalysis.errors import UniverseLoadError
from lammps_trajectory_analysis_tools.integrations.mdanalysis.selection import select_atoms
from lammps_trajectory_analysis_tools.lib.data_types import AtomCoordinates, AtomPairs, Box, MDA_Universe


def load_universe(topology_path: str, trajectory_source: Any, **kwargs: Any) -> mda.Universe:
    """Create an MDAnalysis Universe from topology and trajectory inputs.

    Args:
        topology_path: Path to the topology file.
        trajectory_source: Path or in-memory trajectory source accepted by
            ``MDAnalysis.Universe``.
        **kwargs: Additional keyword arguments passed to MDAnalysis.Universe.

    Returns:
        The initialized MDAnalysis Universe object.

    Raises:
        UniverseLoadError: If MDAnalysis fails to build the universe.
    """
    try:
        return mda.Universe(topology_path, trajectory_source, **kwargs)
    except Exception as exc:  # pragma: no cover - passthrough wrapper
        raise UniverseLoadError(str(exc)) from exc


def calculate_atom_pairs(atom_coordinates: AtomCoordinates,
                         cutoff: float,
                         box: Box) -> AtomPairs:
    """Calculate unique atom pairs within the provided cutoff.

    The algorithm assumes periodic boundary conditions for a right rectangular
    simulation box.

    Args:
        atom_coordinates: Atomic coordinates with shape ``(n_atoms, 3)``.
        cutoff: Neighbor-search cutoff in angstroms.
        box: Box dimensions with shape ``(6,)``.

    Returns:
        Atom-pair indices with shape ``(n_pairs, 2)``.
    """
    kdtree = PeriodicKDTree(box=box)
    kdtree.set_coords(atom_coordinates, cutoff)
    pairs = kdtree.search_pairs(cutoff)
    return pairs


def calculate_atom_pairs_vectors(universe: MDA_Universe,
                                 pairs: AtomPairs) -> AtomCoordinates:
    """Calculate pair displacement vectors with periodic-boundary wrapping.

    For each pair ``(i, j)`` this returns ``r_j - r_i`` adjusted by periodic
    boundary conditions.

    Args:
        universe: MDAnalysis universe positioned at the frame of interest.
        pairs: Atom-pair indices with shape ``(n_pairs, 2)``.

    Returns:
        Pair displacement vectors with shape ``(n_pairs, 3)``.
    """
    box_lengths = universe.dimensions[0:3]

    initial_atoms_indices_data = pairs[:, 0:1]
    initial_atoms_indices = initial_atoms_indices_data.flatten()
    initial_atoms_group = universe.atoms[initial_atoms_indices]
    initial_atoms_positions = initial_atoms_group.positions

    final_atoms_indices_data = pairs[:, 1:2]
    final_atoms_indices = final_atoms_indices_data.flatten()
    final_atoms_group = universe.atoms[final_atoms_indices]
    final_atoms_positions = final_atoms_group.positions

    disp_vectors = final_atoms_positions - initial_atoms_positions
    pbc_delta = box_lengths * np.round(disp_vectors / box_lengths)
    atom_pair_vectors = disp_vectors - pbc_delta

    return atom_pair_vectors


def get_universe_data_for_lop_fcc_sf(universe_mda: MDA_Universe,
                                     cutoff: float,
                                     selection_query: str) -> tuple[mda.AtomGroup, AtomCoordinates, Box, AtomPairs, AtomCoordinates]:
    """Collect per-frame data needed by the LOP SF FCC workflow.

    Args:
        universe_mda: MDAnalysis universe positioned at the current frame.
        cutoff: Neighbor-search cutoff in angstroms.
        selection_query: MDAnalysis atom-selection expression to limit the
            atoms considered for the frame.

    Returns:
        A tuple containing the selected atom group, the selected coordinates,
        the box dimensions, the atom-pair indices, and the atom-pair vectors.
    """
    selected_atoms = select_atoms(universe_mda, selection_query)
    atom_coordinates = np.asarray(selected_atoms.positions, dtype=np.float32)
    box = np.asarray(universe_mda.dimensions, dtype=np.float32)
    atom_pairs = calculate_atom_pairs(atom_coordinates, cutoff, box)
    atom_pair_vectors = calculate_atom_pairs_vectors(universe_mda, atom_pairs)
    return selected_atoms, atom_coordinates, box, atom_pairs, atom_pair_vectors
