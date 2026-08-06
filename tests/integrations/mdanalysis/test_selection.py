#! /usr/bin/env python3

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.selection import select_atoms
from tests.input_files.Ar4Version0 import Ar4Version0


def test_select_atoms_all_returns_expected_atom_count() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    atom_group = select_atoms(universe, "all")

    assert atom_group.n_atoms == test_config.nm_atoms
