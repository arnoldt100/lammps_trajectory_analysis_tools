#! /usr/bin/env python3

# Python standard library imports
import unittest

# Third party library imports
import numpy as np

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from data_types import AtomCoordinates


class TestLopSfFcc(unittest.TestCase):
    def test_lop_sf_fcc_single_atom(self):
        atom_coordinates  : AtomCoordinates = np.zeros((3,1),dtype=np.float64)
        value = calculate_sf_fcc_order_parameter(atom_coordinates)
        self.assertAlmostEqual(value,0.00000,places=3)

# ----------
# Public members
# ----------

if __name__ == "__main__":
    unittest.main()
