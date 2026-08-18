# Third party library imports
import enum
import pytest
import numpy as np
import numpy.typing as npt

# Local Library package imports
from tests.input_files.Ar4Version0 import Ar4Version0
from lammps_trajectory_analysis_tools.lib.data_types import (
    AtomCoordinates,
    AtomPairs,
    LatticeVectors,
    MDA_Universe)

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc import ( 
    calculate_sf_fcc_atom_order_parameter_no_coeffs,
    calculate_sf_fcc_atom_order_parameter_with_coeffs,
    calculate_lop_fcc_exp_terms, 
    calculate_lop_fcc_atom_pair_exp_terms,
    create_atom_pair_key)

from lammps_trajectory_analysis_tools.lib.accumulator.array_accumulator import ArrayAccumulator

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
    def incorrect_exp_terms(cls,
            atom1_index: np.int32,
            atom2_index: np.int32,
            dr: np.ndarray ,
            wavevectors: np.ndarray ,
            ref_exp_terms: np.ndarray,
            experimental_exp_terms: np.ndarray)->str:
        """ Creates an error meessage for incorect exp terms.

        Args:
            atom1_index : The index of the initial atom.
            atom2_index : The index of the destination atom.
            dr : The displacement vector from atom1 to atom2.

        Returns:
            Returns a string. The string contains the following information:
                * The atom pair indices 
                * The displacement vector form atom1 to atom atom2
                * The wave vector terms
                * The reference exp terms
                * The programatically calculated exp terms

        """
        message  = f"\nAtoms pairs indices, {atom1_index} and {atom2_index}, have incorrect exp terms."
        message += f"\nwavevectors = {wavevectors}\n\n"
        message += f"dr = {dr}\n\n"
        message += "exp terms\n"
        message += f"experimental    reference\n"
        message += f"-------------------------\n"
        for idx,value in enumerate(ref_exp_terms):
            message += f"{experimental_exp_terms[idx]} , {ref_exp_terms[idx]}\n"
        return message

def test_lop_sf_fcc_atom_order_parameter_with_coeffs(ar4_version0):
    rtolerance = 1e-5
    atolerance = 1e-8

    [my_test_configuration,my_test_configuration_universe] = ar4_version0

    atom_accum_exp_terms_nocoeffs = my_test_configuration.atom_accum_exp_terms_nocoeffs
    nm_wavevectors = my_test_configuration.nm_wavevectors
    accum_lop_nm_neighbors = my_test_configuration.accum_lop_nm_neighbors
    nm_atoms = my_test_configuration.nm_atoms

    programatic_values = calculate_sf_fcc_atom_order_parameter_with_coeffs(nm_atoms,
                                                                           nm_wavevectors,
                                                                           atom_accum_exp_terms_nocoeffs.finalize(),
                                                                           accum_lop_nm_neighbors)

    reference_values = my_test_configuration.atom_accum_exp_terms_with_coeffs
    np.testing.assert_allclose(programatic_values,
                               reference_values,
                               rtol=rtolerance,
                               atol=atolerance,
                               equal_nan=False,
                               strict=True)

def test_lop_sf_fcc_atom_order_parameter_no_coeffs(ar4_version0):
    rtolerance = 1e-5
    atolerance = 1e-8

    [my_test_configuration,my_test_configuration_universe] = ar4_version0

    (programatic_values,programatic_nm_neighbors) = (
        calculate_sf_fcc_atom_order_parameter_no_coeffs(my_test_configuration_universe,
        my_test_configuration.wave_vectors,
        my_test_configuration.cutoff) )

    reference_values = my_test_configuration.atom_accum_exp_terms_nocoeffs

    np.testing.assert_allclose(programatic_values,
                               reference_values.finalize(),
                               rtol=rtolerance,
                               atol=atolerance,
                               equal_nan=False,
                               strict=True)


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

        error_message = ErrMsgLopFccExpTerms.incorrect_exp_terms(
                atom_pair[0],
                atom_pair[1],
                dr,
                wave_vectors,
                reference_atom_pairs_exp_terms[key],
                accumulator_exp_x.finalize())


        np.testing.assert_allclose(accumulator_exp_x.finalize(),
                                   reference_atom_pairs_exp_terms[key],
                                   rtol=rtolerance,
                                   atol=atolerance,
                                   equal_nan=False,
                                   strict=True,
                                   err_msg=error_message)


