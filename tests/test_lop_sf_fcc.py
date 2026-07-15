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
        cls.edge_length = np.float32(5.19) # Edge length in angstroms.
        cls.volume = cls.edge_length ** 3
        cls.a = np.array([0,1,1], dtype=np.float32)
        cls.b = np.array([1,0,1], dtype=np.float32)
        cls.c = np.array([1,1,0], dtype=np.float32)
        cls.primitive_lattice_vectors = np.array([cls.a,cls.b,cls.c],dtype=np.float32)
        cls.k_a = np.cross(cls.b,cls.c)
        cls.k_b = np.cross(cls.c,cls.a)
        cls.k_c = np.cross(cls.a,cls.b)
        cls.reciprocal_lattice_vectors = (2.0*np.pi/cls.volume)*np.array([cls.k_a,cls.k_b,cls.k_c],dtype=np.float32)



    def test_lop_sf_fcc_1(self):

        # First we form a single DCD trajectory.
        box_dimensions = (
            np.array([self.edge_length,
                      self.edge_length,
                      self.edge_length,
                      90.0, 90.0, 90.0],dtype=np.float32))

        neighbor_cutoff = self.edge_length/2.0

        atom_coordinates = self.edge_length*np.array(
             [[0.00,  0.00, 0.00],
              self.a,
              self.b,
              self.c],dtype=np.float32)

        single_frame_trajectory = np.expand_dims(self.atom_coordinates,axis=0)

        # Next we define the wave vectors for the order parameter.
        k_0 = np.array([1.00, 0.00, 0.00],dtype=np.float64)
        k_1 = np.array([0.00, 1.00, 0.00],dtype=np.float64)
        k_2 = np.array([0.00, 0.00, 1.00],dtype=np.float64)
        k_3 = np.array([1.00, 1.00, 0.00],dtype=np.float64)
        k_4 = np.array([1.00, -1.00, 0.00],dtype=np.float64)
        k_5 = np.array([0.00, 1.00, 1.00],dtype=np.float64)
        normalized_wave_vectors: WaveVectors = (
            (2.00/np.pi)*(1.00/cls.edge_length)*(np.array([k_0,k_1,k_2,k_3,k_4,k_5],dtype=np.float64)))


        value = calculate_sf_fcc_order_parameter(copy.deepcopy(self.atom_coordinates),
                        self.normalized_wave_vectors,
                        self.neighbor_cutoff,
                        self.box_dimensions)
        self.assertAlmostEqual(value,0.00000,places=3)

    @classmethod
    def tearDownClass(cls):
        pass
# ----------
# Public members
# ----------

if __name__ == "__main__":
    unittest.main()
