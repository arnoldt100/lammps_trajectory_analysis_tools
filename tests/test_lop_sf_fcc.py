#! /usr/bin/env python3

# Python standard library imports
import unittest

# Third party library imports
import numpy as np

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from data_types import AtomCoordinates


class TestLopSfFcc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        """ A FCC cubic structure with an edge length equal to 5.19 angstroms"""
        cls.edge_length = np.float64(5.19)

        cls.neighbor_cutoff = 2.0*np.float64(cls.edge_length)

        cls.atom_coordinates =  cls.edge_length*np.array(
             [[0.00,  0.00, 0.00],
              [0.50, 0.50, 0.00],
              [0.50, 0.00, 0.50],
              [0.00,  0.50, 0.50],
              [0.00,  0.00, 1.00],
              [0.50, 0.50, 1.00],
              [0.00,  1.00, 0.00],
              [0.50, 1.00, 0.50],
              [0.00,  1.00, 1.00],
              [1.00, 0.00, 0.00],
              [1.00, 0.50, 0.50],
              [1.00, 0.00, 1.00],
              [1.00, 1.00, 0.00],
              [1.00, 1.00, 1.00]],dtype=np.float64)

        k_0 = np.array([1.00, 0.00, 0.00],dtype=np.float64)
        k_1 = np.array([0.00, 1.00, 0.00],dtype=np.float64)
        k_2 = np.array([0.00, 0.00, 1.00],dtype=np.float64)
        k_3 = np.array([1.00, 1.00, 0.00],dtype=np.float64)
        k_4 = np.array([1.00, -1.00, 0.00],dtype=np.float64)
        k_5 = np.array([0.00, 1.00, 1.00],dtype=np.float64)
        cls.wave_vectors = (2.00/np.pi)*(1.00/cls.edge_length)*(np.array([k_0,k_1,k_2,k_3,k_4,k_5] ,dtype=np.float64))

    def test_lop_sf_fcc_single_atom(self):
        r_0 : AtomCoordinates = self.atom_coordinates[0,:]
        print (f"r_0: {r_0}")
        value = calculate_sf_fcc_order_parameter(self.atom_coordinates)
        self.assertAlmostEqual(value,0.00000,places=3)

    @classmethod
    def tearDownClass(cls):
        pass
# ----------
# Public members
# ----------

if __name__ == "__main__":
    unittest.main()
