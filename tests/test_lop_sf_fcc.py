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
from lop_sf_fcc.lop_sf_fcc import calculate_atom_pairs
from data_types import LatticeVectors, AtomCoordinates
from tests.input_files.Ar4Version0 import Ar4Version0

all_test_structures = [Ar4Version0]

class TestLopSfFcc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Creates an MDAnalysis universe of 4 Ar atoms.

        Given an FCC lattice with edge length "edge_length", a FCC structure of
        4 atoms is created. The atoms are then placed in a cubic box where each
        side is length 10*edge_length. The PSF file is read from disk. The
        number of atoms must be 4 atoms to match the PSF file. The atomic coordinates,
        box dimensions, and PSF are then used to create a single frame MDAnalysis universe
        for testing purposes.
        """

        cls.test_cases = [Ar4Version0()]

        cls.test_cases = []
        for test_item in all_test_structures:
           test_configuration = test_item()
           test_configuration_universe = test_configuration.create_md_analysis_universe()
           cls.test_cases.append((test_configuration,test_configuration_universe))

    def test_rlv_plv_orthogonal(self):
        """ Verifies the orthogonality of the principal and reciprocal lattice vectors.

        Given principal lattice vectors a, b and c,
        reciprocal lattice vector k_a is formed by k_a = (1/(2*pi*vol))bxc
        where vol = (axb)*c. This means k_a*b and k_a*c must equal 0. Similarly for
        k_b and k_c.
        """
        # The number of decimal places to compare that the dot products are
        # zero.
        places = 15

        # Indices 0, 1, and 2 respectively correspond to axis x,y and z.
        # The reciprocal lattice vectors are as follows:
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

        for (test_structure,_) in self.test_cases:
            test_structure_identification = test_structure.structure_identification

            # We loop over the reciprocal and primitive lattice vector indices
            # and verify the corresponding reciprocal and lattice vector dot
            # product is zero.
            for [rlv_index,plv_index] in indices_to_verify:
                message = _message_rlvplv_nonorthogonal(test_structure_identification,
                                                        rlv_index,test_structure.reciprocal_lattice_vectors[rlv_index,:],
                                                        plv_index,test_structure.primitive_lattice_vectors[plv_index,:])
                dp = np.dot(test_structure.reciprocal_lattice_vectors[rlv_index,:],
                            test_structure.primitive_lattice_vectors[plv_index,:])
                self.assertAlmostEqual(dp,0.00,places,message)

    def test_neighbor_atom_pairs(self):
        """ Verifies the correct atom neighbor pairs are formed for each test case
        """
        for (test_structure,test_universe) in self.test_cases:
            test_structure_identification = test_structure.structure_identification

            # Get the correct atom pairs for the test structure.
            correct_atom_pairs = test_structure.correct_atom_pairs

            # Compute the atom pairs for the MDAnalysis universe as done in the
            # "lop_sf_fcc.py" module.
            all_atoms = test_universe.select_atoms("all")
            atom_coordinates = all_atoms.positions
            box = test_universe.dimensions
            cutoff = test_structure.cutoff
            exp_atom_pairs = calculate_atom_pairs(atom_coordinates,cutoff,box)

            # The exp_atom_pairs must have unique pairs.
            exp_atom_pairs_unique,exp_counts = (
                np.unique(exp_atom_pairs,axis=0,return_counts=True))
            message = _message_non_unique_pairs(test_structure_identification,
                                                exp_atom_pairs_unique,
                                                exp_counts)
            self.assertEqual(exp_counts.all() == 1,True,message)

            # The exp_atom_pairs_unique must equal the correct_atom_pairs.
            correct_atom_pairs_unique = np.unique(correct_atom_pairs,axis=0)
            message = _message_incorrect_atom_pairs(test_structure_identification,
                                                    exp_atom_pairs_unique,
                                                    correct_atom_pairs)
            self.assertEqual(np.array_equal(exp_atom_pairs_unique,correct_atom_pairs_unique),True,message)

    def test_reciprocal_lattice_vectors(self):
        """ Test if the reciprocal lattice vectors are correct."""
        for (test_structure,test_universe) in self.test_cases:
            test_structure_identification = test_structure.structure_identification
            edge_length = test_structure.lattice_edge_length
            exp_reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(edge_length )
            correct_reciprocal_lattice_vectors = test_structure.reciprocal_lattice_vectors

            # The number of decimal places to compare the local FCC order parameter.
            tolerance = 1e-8
            close_enough = np.allclose(exp_reciprocal_lattice_vectors,correct_reciprocal_lattice_vectors,atol=tolerance)

    # def test_fcc_ar4(self):
    #     # The number of decimal places to compare the local FCC order parameter.
    #     places = 15
    #     message = _message_a4_lop_sf()
    #     cutoff = self.cutoff

    #     box_dimensions =  self.universe.dimensions
    #     for ts in self.universe.trajectory:
    #         value = calculate_sf_fcc_order_parameter(self.universe,
    #                                          self.wave_vectors,
    #                                          cutoff)

    #     self.assertAlmostEqual(value,0.00,places,message)

    @classmethod
    def tearDownClass(cls):
        pass
#
# ----------
# Private members
# ----------

def _message_rlvplv_nonorthogonal(test_structure_identification,
                                  rlv_index: int, rlv: LatticeVectors,
                                  plv_index: int, plv: LatticeVectors)->str:
    """ Returns a string warning message that RLV and PLV vectors aren't orthogonal.

    rlv_index : The array index of the reciprocal lattice vector.

    rlv : A reciprocal lattice vector.

    plv_index : The array index of the principal lattice vector.

    plv : A principal lattice vector.

    """
    message = f"\nThe {test_structure_identification} index {rlv_index} reciprocal lattice vector isn't orthogonal\n"
    message += f"to the {plv_index} index primitive lattice vector.\n"
    message += f"reciprocal_lattice_vector[{rlv_index}]={rlv}\n"
    message += f"primitive_lattice_vector[{plv_index}]={plv}\n"
    return message

def _message_non_unique_pairs(test_structure_identification,
                              atoms_pairs,atom_pairs_counts )->str:
    message = f"\nThe {test_structure_identification} has some nonunique atom pairs.\n"
    message += f"The atom pairs found are:\n{atoms_pairs}\n"
    message += f"The atom pairs counts are:\n{atom_pairs_counts}\n"
    return message

def _message_incorrect_atom_pairs(test_structure_identification,
                                  exp_atom_pairs,correct_atom_pairs)->str:
    message = f"\nThe {test_structure_identification} has some incorect atom pairs.\n"
    message += f"The experimental atom pairs found are:\n{exp_atom_pairs}\n"
    message += f"The correct atom pairs are:\n{correct_atom_pairs}\n"
    return message

def _message_a4_lop_sf():
    message = "The local order parameter fcc structure factor is wrong."
    return message

if __name__ == "__main__":
    unittest.main()
