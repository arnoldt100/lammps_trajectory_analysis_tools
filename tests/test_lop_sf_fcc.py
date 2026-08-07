#! /usr/bin/env python3

# Python standard library imports
import unittest

# Third party library imports
import numpy as np
import numpy.typing as npt

# Local Library package imports
from lammps_trajectory_analysis_tools.lib.data_types import (
    AtomCoordinates,
    AtomPairs,
    LatticeVectors,
    MDA_Universe)

from lammps_trajectory_analysis_tools.integrations.mdanalysis.universe import (
    calculate_atom_pairs,
    calculate_atom_pairs_vectors,
)

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc import (
    create_reciprocal_lattice_vectors,
    create_wavevectors)

from tests.input_files.Ar4Version0 import Ar4Version0

all_test_structures = [Ar4Version0]

class TestLopSfFcc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Creates an MDAnalysis universe of 4 Ar atoms.

        Given an FCC lattice with edge length "edge_length", a FCC structure of
        4 atoms is created. The atoms are then placed in a cubic box where each
        side is length 10*edge_length. The PSF file is read from disk. The
        number of atoms must be 4 atoms to match the PSF file. The atomic 
        coordinates, box dimensions, and PSF are then used to create a single 
        frame MDAnalysis universe for testing purposes.
        """

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
                message = _message_rlvplv_nonorthogonal(
                    test_structure_identification,
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
            reference_atom_pairs = test_structure.atom_pairs

            # Compute the atom pairs for the MDAnalysis universe as done in the
            # "lop_sf_fcc.py" module.
            cutoff = test_structure.cutoff
            exp_atom_pairs = _get_programmatical_atom_pairs_from_universe(test_universe,cutoff)

            # The exp_atom_pairs must have unique pairs.
            exp_atom_pairs_unique,exp_counts = (
                np.unique(exp_atom_pairs,axis=0,return_counts=True))
            message = _message_non_unique_pairs(test_structure_identification,
                                                exp_atom_pairs_unique,
                                                exp_counts)
            self.assertEqual(exp_counts.all() == 1,True,message)

            # The exp_atom_pairs_unique must equal the reference_atom_pairs.
            correct_atom_pairs_unique = np.unique(reference_atom_pairs,axis=0)
            message = _message_incorrect_atom_pairs(test_structure_identification,
                                                    exp_atom_pairs_unique,
                                                    reference_atom_pairs)
            self.assertEqual(np.array_equal(exp_atom_pairs_unique,correct_atom_pairs_unique),True,message)

    def test_reciprocal_lattice_vectors(self):
        """ Test if the reciprocal lattice vectors are correct."""
        # The number of decimal places to compare the local FCC order parameter.
        tolerance = 1e-8

        for (test_structure,test_universe) in self.test_cases:
            test_structure_identification = test_structure.structure_identification
            edge_length = test_structure.lattice_edge_length
            exp_reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(edge_length)
            correct_reciprocal_lattice_vectors = test_structure.reciprocal_lattice_vectors

            close_enough = np.allclose(exp_reciprocal_lattice_vectors,
                                       correct_reciprocal_lattice_vectors,
                                       atol=tolerance)
            message = _message_incorrect_reciprocal_lattice_vectors(
                test_structure_identification,
                exp_reciprocal_lattice_vectors,
                correct_reciprocal_lattice_vectors)
            self.assertEqual(close_enough,True,message)

    def test_wave_vectors(self):
        """
        Verify that the generated experimental wave vectors match the expected reference values.

        Compares the programmatically generated 'exp_wave_vectors' against the
        definitive 'reference_wave_vectors'. The test passes if the difference
        between the two sets falls within the specified numerical tolerance.
        """
        # The tolerance for comparing the "exp_wave_vectors"
        # and "reference_wave_vectors".
        tolerance = 1e-8

        for (test_structure,test_universe) in self.test_cases:
            # Define the identification of this test.
            test_structure_identification = test_structure.structure_identification

            # Create the experimental and correct wavevectors.
            edge_length = test_structure.lattice_edge_length
            exp_wave_vectors = create_wavevectors(edge_length)
            reference_wave_vectors = test_structure.wave_vectors

            # Define the message for test failure.
            message = _message_incorrect_wave_vectors(test_structure_identification,
                                                      exp_wave_vectors,
                                                      reference_wave_vectors)

            # Check if exp_wave_vectors are within tolerance of the correct wavevectors.
            close_enough = np.allclose(exp_wave_vectors,reference_wave_vectors,atol=tolerance)
            self.assertEqual(close_enough,True,message)

    def test_atom_pairs_vectors(self):
        """
        Verify that the generated atom pair vectors match the expected reference values.

        Compares the programmatically generated 'atom_pair__vectors' against the
        definitive 'reference_atom_pair_vectors'. The test passes if the difference
        between the two sets falls within the specified numerical tolerance.
        """

        # The tolerances for comparing the "exp_atom_pairs_vectors"
        # and "reference_atom_pair_vectors".
        rtolerance = 1e-5
        atolerance = 1e-8

        for (test_structure,test_universe) in self.test_cases:
            # The cutoff distance for chosing the atom pairs.
            cutoff = test_structure.cutoff

            # Define the identification of this test.
            test_structure_identification = test_structure.structure_identification

            # Get the exp atom pairs vectors.
            exp_atom_pair_vectors = (
                _get_programmatical_atom_pairs_vectors_from_universe(test_universe,cutoff))

            # Get the reference atom pairs vectors.
            reference_atom_pair_vectors = test_structure.atom_pairs_vectors
 
            # Define the message for test failure.
            message = _message_incorrect_atom_pairs_vectors(test_structure_identification,
                                                            exp_atom_pair_vectors,
                                                            reference_atom_pair_vectors)

            # Check if the exp_atom_pairs_vectors are within tolerance of
            # reference_atom_pair_vectors.
            close_enough = np.allclose(exp_atom_pair_vectors,
                                       reference_atom_pair_vectors,
                                       atol=atolerance,
                                       rtol=rtolerance)
            self.assertEqual(close_enough,True,message)

    @classmethod
    def tearDownClass(cls):
        pass
#
# ----------
# Private members
# ----------

def _get_programmatical_atom_pairs_from_universe(universe: MDA_Universe,
        cutoff: np.float64 )->AtomPairs:
    """ Get the programtic atom pairs of from the universe.

    Given a MDAnalysis universe that is periodic with a right rectangular prism
    bounding box, we calculate all atom pairs that are within "cutoff" distance
    of each other.

    Args:
        universe: The MDAnalysis universe.

        cutoff: The cutoff to search for neighboring atoms.

    """
    all_atoms = universe.select_atoms("all")
    atom_coordinates = all_atoms.positions
    box = universe.dimensions
    exp_atom_pairs = calculate_atom_pairs(atom_coordinates,cutoff,box)
    return exp_atom_pairs

def _get_programmatical_atom_pairs_vectors_from_universe(universe: MDA_Universe,
        cutoff: np.float64 )->AtomCoordinates:
    """Get the programatic atom pairs vectors from the universe.

    Args:
        universe: The MDAnalysis universe.

        cutoff: The cutoff to search for neighboring atoms pairs to form the
        atom pair vectors.

    """
    atom_pairs = _get_programmatical_atom_pairs_from_universe(universe,cutoff)
    atom_pairs_vectors = calculate_atom_pairs_vectors(universe,atom_pairs)
    return atom_pairs_vectors

def _message_rlvplv_nonorthogonal(test_structure_identification: str,
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

def _message_incorrect_wave_vectors(test_structure_identification,
                                    exp_wave_vectors,correct_wave_vectors)->str:
    message = f"\nThe {test_structure_identification} has some incorect wave vectors.\n"
    message += f"The experimental wave vectors found are:\n{exp_wave_vectors}\n"
    message += f"The correct wave vectors are:\n{correct_wave_vectors}\n"
    return message

def _message_incorrect_reciprocal_lattice_vectors(test_structure_identification,
                                                  exp_reciprocal_lattice_vectors,
                                                  correct_reciprocal_lattice_vectors)->str:
    message = f"\nThe {test_structure_identification} has some incorect reciprocal lattice vectors.\n"
    message += f"The experimental reciprocal lattice vectors found are:\n{exp_reciprocal_lattice_vectors}\n"
    message += f"The correct reciprocal lattice vectors are:\n{correct_reciprocal_lattice_vectors}\n"
    return message

def _message_incorrect_atom_pairs_vectors(test_structure_identification,
                                  exp_atom_pairs,
                                  reference_atom_pairs_vectors)->str:
    message = f"\nThe {test_structure_identification} has some incorect atom pairs vectors.\n"
    message += f"The experimental atom pairs vectors found are:\n{exp_atom_pairs}\n"
    message += f"The reference atom pairs vectors are:\n{reference_atom_pairs_vectors}\n"
    return message

if __name__ == "__main__":
    unittest.main()
