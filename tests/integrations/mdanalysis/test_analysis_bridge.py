#! /usr/bin/env python3

# Third party imports
import numpy as np

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.analysis_bridge import run_lop_sf_fcc_from_universe
from tests.input_files.Ar4Version0 import Ar4Version0


def test_run_lop_sf_fcc_from_universe_matches_reference_coordinates() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    bridge_coordinates = run_lop_sf_fcc_from_universe(universe)

    assert bridge_coordinates.shape == test_config.coordinates.shape
    np.testing.assert_allclose(bridge_coordinates, test_config.coordinates)
