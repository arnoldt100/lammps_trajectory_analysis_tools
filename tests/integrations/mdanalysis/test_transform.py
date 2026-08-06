#! /usr/bin/env python3

# Third party imports
import numpy as np

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.transform import center_coordinates
from tests.input_files.Ar4Version0 import Ar4Version0


def test_center_coordinates_has_zero_centroid() -> None:
    test_config = Ar4Version0()

    centered_coordinates = center_coordinates(test_config.coordinates)

    np.testing.assert_allclose(np.mean(centered_coordinates, axis=0), np.zeros(3), atol=1e-12)
