#! /usr/bin/env python3

# Third party imports
import numpy as np
import pytest
from MDAnalysis.coordinates.memory import MemoryReader

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.errors import UniverseLoadError
from lammps_trajectory_analysis_tools.integrations.mdanalysis.universe import load_universe
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
