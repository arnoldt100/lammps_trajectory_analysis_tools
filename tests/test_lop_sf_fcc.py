#! /usr/bin/env python3

# Python standard library imports
import unittest
import os

# Third party library imports
import numpy as np
import numpy.typing as npt
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from lop_sf_fcc.lop_sf_fcc import create_wavevectors
from lop_sf_fcc.lop_sf_fcc import create_reciprocal_lattice_vectors
from lop_sf_fcc.lop_sf_fcc import create_primitive_lattice_vectors
from data_types import LatticeVectors, AtomCoordinates


class TestLopSfFcc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        """ A FCC structure of 4 atoms with an edge length equal to 1.00 angstroms"""
        cls.fcc_coordinates : AtomCoordinates = np.array([
            [0.00,0.00,0.00],
            [0.50,0.50,0.00],
            [0.50,0.00,0.50],
            [0.00,0.50,0.50]])

        # We define the edge length of the FCC lattice structure.
        cls.edge_length = np.float64(5.19) # Edge length in angstroms.


        """ The atoms atomic coordinates. """
        cls.atomic_coordinates : AtomCoordinates = cls.edge_length*cls.fcc_coordinates

        cls.primitive_lattice_vectors : LatticeVectors = create_primitive_lattice_vectors(cls.edge_length)
        cls.reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(cls.edge_length)
        cls.wave_vectors = create_wavevectors(cls.edge_length)

        # Create box dimensions for a single frame Format: [lx, ly, lz, alpha, beta, gamma]
        cls.box_dimensions = (
            np.array([[cls.edge_length,cls.edge_length,cls.edge_length,
                      90.0, 90.0, 90.0]],dtype=np.float64))

        """ The absolute path to the protein """
        cls.psf_filepath: str = os.path.join(os.getenv("LTAT_TOP_LEVEL"),"tests","input_files","ar4.psf") 

        """ The units of the time step"""
        cls.timeunits: str = "ps"

        """ The magnitude of the time step. """
        cls.dt: float = 1.0

        # Create a Ad Analysis universe for a single frame.
        cls.u = _create_universe(cls.atomic_coordinates, cls.box_dimensions,
                                 cls.psf_filepath, cls.timeunits,
                                 cls.dt)

    def test_rlv_plv_orthogonal(self):
        """ This test verifies the orthogonality of the principal and reciprocal lattice vectors.

        Given principal lattice vectors a, b and c,
        reciprocal lattice vector k_a is formed by k_a = (1/(2*pi*vol))bxc
        where vol = (axb)*c. This means k_a*b and k_a*c must equal 0. Similarly for
        k_b and k_c.
        """

        # The number of decimal places to compare that the dot products are
        # zero.
        places = 15

        # Indices 0, 1, and 2 respectively correspond to axis x,y and z.
        # Therefore reciprocal lattice 
        #   k_a = (1/(2*pi*vol))bxc --> reciprocal lattice vector with index 0 is perpendicular
        #   to principal lattice vectors with indices 1 and 2.
        #   k_b = (1/(2*pi*vol))cxa --> reciprocal lattice vector with index 1 is perpendicular
        #   to principal lattice vectors with indices 2 and 0.
        #   k_c = (1/(2*pi*vol))axb --> reciprocal lattice vector with index 2 is perpendicular
        #   to principal lattice vectors with indices 0 and 1.
        (rlv_a_index,rlv_b_index,rlv_c_index) = (0,1,2)
        (plv_a_index,plv_b_index,plv_c_index) = (0,1,2)
        indices_to_verify = np.array([[rlv_a_index,plv_b_index],
                            [rlv_a_index,plv_c_index],
                            [rlv_b_index,plv_c_index],
                            [rlv_b_index,plv_a_index],
                            [rlv_c_index,plv_a_index],
                            [rlv_c_index,plv_b_index]])

        # We loop over the reciprocal and primitive lattice vector indices
        # and verify the corresponding reciprocal and lattice vector dot
        # product is zero.
        for [rlv_index,plv_index] in indices_to_verify:
            message = _message_rlvplv_nonorthogonal(rlv_index,self.reciprocal_lattice_vectors[rlv_index,:],
                                                   plv_index,self.primitive_lattice_vectors[plv_index,:])
            dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                        self.primitive_lattice_vectors[plv_index,:])
            self.assertAlmostEqual(dp,0.00,places,message)


    def test_fcc_ar4(self):
        # The number of decimal places to compare the local FCC order parameter.
        places = 15
        message = _message_a4_lop_sf()
        value = 0.01
        self.assertAlmostEqual(value,0.00,places,message)

    @classmethod
    def tearDownClass(cls):
        pass
#
# ----------
# Private members
# ----------

def _message_rlvplv_nonorthogonal(rlv_index: int, rlv: LatticeVectors,
                                 plv_index: int, plv: LatticeVectors)->str:
    """ Returns a string warning message that RLV and PLV vectors aren't orthogonal.

    rlv_index : The array index of the reciprocal lattice vector.

    rlv : A reciprocal lattice vector.

    plv_index : The array index of the principal lattice vector.

    plv : A principal lattice vector.

    """
    # The 1 index primitive lattice vector should be orthogonal to
    # the 2 and 0 index reciprocal lattice vectors.
    plv_index = 1
    rlv_index = 2
    message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
    message += f"to the {plv_index} index primitive lattice vector./n"
    message += f"reciprocal_lattice_vector[{rlv_index}]={rlv}/n"
    message += f"primitive_lattice_vector[{plv_index}]={plv}/n"
    return message

def _message_a4_lop_sf():
    message = "The local order parameter fcc structure factor is wrong."
    return message

def _create_universe(atom_coordinates: AtomCoordinates, box_dimensions, psf_filepath: str,
                     timeunits: str, dt: float):
    single_frame_trajectory = np.expand_dims(atom_coordinates, axis=0)
    single_box_dimensions = np.expand(box_dimensions,axis=0)
    universe = mda.Universe(psf_filepath,
            single_frame_trajectory,
            format=MemoryReader,
            dimensions=box_dimensions)
    return universe

if __name__ == "__main__":
    unittest.main()
