#! /usr/bin/env python3

# Python standard library imports
import unittest
import copy

# Third party library imports
import numpy as np
from MDAnalysis.lib.nsgrid import FastNS

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from data_types import AtomCoordinates
from data_types import WaveVectors


class TestLopSfFcc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        """ A FCC cubic structure with an edge length equal to 5.19 angstroms"""
        cls.edge_length = np.float32(5.19)
        cls.box_buffer = 0.0
        cls.neighbor_cutoff = cls.edge_length/2.0

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
              [1.00, 1.00, 1.00]],dtype=np.float32)

        k_0 = np.array([1.00, 0.00, 0.00],dtype=np.float64)
        k_1 = np.array([0.00, 1.00, 0.00],dtype=np.float64)
        k_2 = np.array([0.00, 0.00, 1.00],dtype=np.float64)
        k_3 = np.array([1.00, 1.00, 0.00],dtype=np.float64)
        k_4 = np.array([1.00, -1.00, 0.00],dtype=np.float64)
        k_5 = np.array([0.00, 1.00, 1.00],dtype=np.float64)
        cls.normalized_wave_vectors: WaveVectors = (
            (2.00/np.pi)*(1.00/cls.edge_length)*(np.array([k_0,k_1,k_2,k_3,k_4,k_5] ,dtype=np.float64)))

        cls.box = np.array([cls.edge_length+cls.box_buffer, cls.edge_length+cls.box_buffer, cls.edge_length+cls.box_buffer,
                            90.0, 90.0, 90.0],dtype=np.float32)

        cls.cutoff = cls.edge_length/2.0

    def test_lop_sf_fcc_(self):
        value = calculate_sf_fcc_order_parameter(copy.deepcopy(self.atom_coordinates),
                        self.normalized_wave_vectors,
                        self.cutoff,
                        self.box)
        self.assertAlmostEqual(value,0.00000,places=3)

    @classmethod
    def tearDownClass(cls):
        pass
# ----------
# Public members
# ----------

if __name__ == "__main__":
    unittest.main()
