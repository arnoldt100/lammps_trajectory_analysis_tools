#! /usr/bin/env python3

# Python standard library imports
import unittest
import copy

# Third party library imports
import numpy as np
from MDAnalysis.coordinates.memory import MemoryReader

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from lop_sf_fcc.lop_sf_fcc import create_wavevectors
from lop_sf_fcc.lop_sf_fcc import create_reciprocal_lattice_vectors
from lop_sf_fcc.lop_sf_fcc import create_primitive_lattice_vectors
from data_types import AtomCoordinates
from data_types import WaveVectors


class TestLopSfFcc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        """ A FCC structure with an edge length equal to 5.19 angstroms"""

        # We define the edge length of the fcc lattice structure.
        cls.edge_length = np.float64(5.19) # Edge length in angstroms.
        cls.primitive_lattice_vectors = create_primitive_lattice_vectors(cls.edge_length)
        cls.reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(cls.edge_length)
        cls.wave_vectors = create_wavevectors(cls.edge_length)

    def test_rlv_plv_orthogonal(self):
        places = 15

        # The 0 index primitive lattice vector should be orthogonal to
        # the 1 and 2 index reciprocal lattice vectors.
        plv_index = 0
        rlv_index = 1
        message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
        message += f"to the {plv_index} index primitive lattice vector./n"
        message += f"reciprocal_lattice_vectors[{rlv_index}]={self.reciprocal_lattice_vectors[rlv_index,:]}"
        message += f"primitive_lattice_vectors[{plv_index}]={self.primitive_lattice_vectors[plv_index,:]}"
        dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                    self.primitive_lattice_vectors[plv_index,:])
        self.assertAlmostEqual(dp,0.00,places,message)

        rlv_index = 2
        message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
        message += f"to the {plv_index} index primitive lattice vector./n"
        message += f"reciprocal_lattice_vectors[{rlv_index}]={self.reciprocal_lattice_vectors[rlv_index,:]}"
        message += f"primitive_lattice_vectors[{plv_index}]={self.primitive_lattice_vectors[plv_index,:]}"
        dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                    self.primitive_lattice_vectors[plv_index,:])
        self.assertAlmostEqual(dp,0.00,places,message)

        # The 1 index primitive lattice vector should be orthogonal to
        # the 2 and 0 index reciprocal lattice vectors.
        plv_index = 1
        rlv_index = 2
        message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
        message += f"to the {plv_index} index primitive lattice vector./n"
        message += f"reciprocal_lattice_vectors[{rlv_index}]={self.reciprocal_lattice_vectors[rlv_index,:]}"
        message += f"primitive_lattice_vectors[{plv_index}]={self.primitive_lattice_vectors[plv_index,:]}"
        dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                    self.primitive_lattice_vectors[plv_index,:])
        self.assertAlmostEqual(dp,0.00,places,message)

        rlv_index = 0
        message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
        message += f"to the {plv_index} index primitive lattice vector./n"
        message += f"reciprocal_lattice_vectors[{rlv_index}]={self.reciprocal_lattice_vectors[rlv_index,:]}"
        message += f"primitive_lattice_vectors[{plv_index}]={self.primitive_lattice_vectors[plv_index,:]}"
        dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                    self.primitive_lattice_vectors[plv_index,:])
        self.assertAlmostEqual(dp,0.00,places,message)

        # The 2 index primitive lattice vector should be orthogonal to
        # the 0 and 1 index reciprocal lattice vectors.
        plv_index = 2
        rlv_index = 0
        message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
        message += f"to the {plv_index} index primitive lattice vector./n"
        message += f"reciprocal_lattice_vectors[{rlv_index}]={self.reciprocal_lattice_vectors[rlv_index,:]}"
        message += f"primitive_lattice_vectors[{plv_index}]={self.primitive_lattice_vectors[plv_index,:]}"
        dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                    self.primitive_lattice_vectors[plv_index,:])
        self.assertAlmostEqual(dp,0.00,places,message)

        rlv_index = 1
        message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
        message += f"to the {plv_index} index primitive lattice vector./n"
        message += f"reciprocal_lattice_vectors[{rlv_index}]={self.reciprocal_lattice_vectors[rlv_index,:]}"
        message += f"primitive_lattice_vectors[{plv_index}]={self.primitive_lattice_vectors[plv_index,:]}"
        dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                    self.primitive_lattice_vectors[plv_index,:])
        self.assertAlmostEqual(dp,0.00,places,message)

    @classmethod
    def tearDownClass(cls):
        pass
#
# ----------
# Private members
# ----------

def MessageTlvRlvOrthogonal()
if __name__ == "__main__":
    unittest.main()
