#! /usr/bin/env python3

# Third party imports
import numpy as np

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.conversion import to_internal_trajectory
from tests.input_files.Ar4Version0 import Ar4Version0


def test_to_internal_trajectory_matches_ar4_reference() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    converted_coordinates = to_internal_trajectory(universe)

    assert converted_coordinates.shape == test_config.coordinates.shape
    np.testing.assert_allclose(converted_coordinates, test_config.coordinates)
