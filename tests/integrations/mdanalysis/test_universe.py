#! /usr/bin/env python3

# Third party imports
import numpy as np
import pytest
from MDAnalysis.coordinates.memory import MemoryReader

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.errors import UniverseLoadError
from lammps_trajectory_analysis_tools.integrations.mdanalysis.universe import (
    calculate_atom_pairs,
    calculate_atom_pairs_vectors,
    load_universe,
)
from tests.input_files.Ar4Version0 import Ar4Version0


def test_load_universe_from_ar4_memory_trajectory() -> None:
    test_config = Ar4Version0()
    trajectory = np.array([test_config.coordinates])
    box_array = np.array([test_config.box])

    universe = load_universe(
        test_config.psf_filepath,
        trajectory,
        format=MemoryReader,
        dt=test_config.timestep,
        dimensions=box_array,
    )

    assert universe.atoms.n_atoms == test_config.nm_atoms


def test_load_universe_raises_integration_error_for_invalid_input() -> None:
    with pytest.raises(UniverseLoadError):
        load_universe("does_not_exist.psf", "does_not_exist.dcd")


def test_calculate_atom_pairs_matches_ar4_reference_pairs() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    atom_coordinates = universe.select_atoms("all").positions
    exp_pairs = calculate_atom_pairs(atom_coordinates, test_config.cutoff, universe.dimensions)

    assert np.array_equal(exp_pairs, test_config.atom_pairs)


def test_calculate_atom_pairs_vectors_matches_ar4_reference_vectors() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    atom_coordinates = universe.select_atoms("all").positions
    atom_pairs = calculate_atom_pairs(atom_coordinates, test_config.cutoff, universe.dimensions)
    exp_vectors = calculate_atom_pairs_vectors(universe, atom_pairs)

    assert np.allclose(exp_vectors, test_config.atom_pairs_vectors, atol=1e-8, rtol=1e-5)
