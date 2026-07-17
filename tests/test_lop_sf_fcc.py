#! /usr/bin/env python3

# Python standard library imports
import unittest
import copy

# Third party library imports
import numpy as np
from MDAnalysis.coordinates.memory import MemoryReader

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from lop_sf_fcc.lop_sf_fcc import create_primitive_wavevectors1
from data_types import AtomCoordinates
from data_types import WaveVectors


class TestLopSfFcc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        """ A FCC structure with an edge length equal to 5.19 angstroms"""

        # We define the edge length of the fcc lattice structure.
        cls.edge_length = np.float64(5.19) # Edge length in angstroms.

        
        cls.reciprocal_lattice_vectors = create_primitive_wavevectors1(cls.edge_length)

    def test_lop_sf_fcc_1(self):
        self.assertAlmostEqual(0.00,0.00,4)

    @classmethod
    def tearDownClass(cls):
        pass
# ----------
# Public members
# ----------

if __name__ == "__main__":
    unittest.main()
