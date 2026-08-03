# Third party library imports
import pytest
import numpy as np
from numpy.typing import npt

# Local Library package imports
from tests.input_files.Ar4Version0 import Ar4Version0
from data_types import (
    AtomCoordinates,
    AtomPairs,
    LatticeVectors,
    MDA_Universe)

from lop_sf_fcc.lop_sf_fcc import ( calculate_sf_fcc_order_parameter,
    calculate_lop_fcc_exp_terms, 
    calculate_lop_fcc_atom_pair_exp_terms,
    create_atom_pair_key)

from accumulator.array_accumulator import ArrayAccumulator

@pytest.fixture
def ar4_version0():
    test_configuration = Ar4Version0()
    test_configuration_universe = test_configuration.create_md_analysis_universe()
    return [test_configuration,test_configuration_universe]

class ErrMsgLopFccExpTerms:
    """A class that generates error meessages."""
    def __init__(self):
        return

    @classmethod
    def incorrect_exp_terms(self,
            atom1_index: np.int32,
            atom2_index: np.int32,
            dr: np.ndarray ,
            wavevectors: np.NDarray[tuple[],dtype=np.float64] ,
            ref_exp_terms: np.ndarray ,
            experimental_exp_terms: np.array)->str:
        """
        Args:
            atom1_index : The index of the initial atom.
            atom2_index : The index of the destination atom.
            dr : The displacement vector from atom1 to atom2.
        """
        message = "Dummy error message"
        return message

def test_lop_fcc_accumulators(ar4_version0):
    message = "The local order parameter fcc structure factor is wrong."
    [my_test_configuration,my_test_configuration_universe] = ar4_version0
    value = calculate_sf_fcc_order_parameter(my_test_configuration_universe,
                                             my_test_configuration.wave_vectors,
                                             my_test_configuration.cutoff)
    assert value == 0.01

def test_lop_fcc_exp_terms(ar4_version0):
    # The tolerances for comparing the exp terms.
    rtolerance = 1e-5
    atolerance = 1e-8

    [my_test_configuration,my_test_configuration_universe] = ar4_version0

    atom_pairs_indices = my_test_configuration.atom_pairs
    atom_pairs_vectors = my_test_configuration.atom_pairs_vectors
    reference_atom_pairs_exp_terms = my_test_configuration.atom_pairs_exp_terms
    wave_vectors = my_test_configuration.wave_vectors
    (nm_wavevectors,_) = wave_vectors.shape
    n_atoms = my_test_configuration_universe.atoms.n_atoms

    for row_id, atom_pair in enumerate(atom_pairs_indices):
        dr = atom_pairs_vectors[row_id]

        key = create_atom_pair_key(*atom_pair)
        accumulator_exp_x = (
            ArrayAccumulator(dtype=np.complex64,capacity=nm_wavevectors,
                             initial_value=np.complex64(0.00),
                             name="wavevector_exp_accumulator"))
        accum1 = calculate_lop_fcc_atom_pair_exp_terms(dr,wave_vectors,accumulator_exp_x)
        print(f"key={key}")
        print(f"accumulator_exp_x={accumulator_exp_x.finalize()}")
        print(f"reference_atom_pairs_exp_terms={reference_atom_pairs_exp_terms[key]}")
        close_enough = np.allocate()

        print(f"testing atom pair {atom_pair}")
        message  = f"For atom indicex {atom_pair[0]} and {atom_pair[1]} we have exp(iq*r) that are not in tolerance.\n"
        message += f"dr={dr}\n"
        for idx, row in enumerate(accumulator_exp_x):
            message += f"  "
        print("\n")

