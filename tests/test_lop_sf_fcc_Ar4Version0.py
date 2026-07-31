# Third party library imports
import pytest
import numpy as np
import numpy.typing as npt

# Local Library package imports
from tests.input_files.Ar4Version0 import Ar4Version0
from data_types import (
    AtomCoordinates,
    AtomPairs,
    LatticeVectors,
    MDA_Universe)

from lop_sf_fcc.lop_sf_fcc import ( calculate_sf_fcc_order_parameter,
    calculate_lop_fcc_exp_terms, create_atom_pair_key)

from accumulator.array_accumulator import ArrayAccumulator
from accumulator.merge_accumulators import merge_array_accumulators

@pytest.fixture
def ar4_version0():
    test_configuration = Ar4Version0()
    test_configuration_universe = test_configuration.create_md_analysis_universe()
    return [test_configuration,test_configuration_universe]

def test_lop_fcc_accumulators(ar4_version0):
    message = "The local order parameter fcc structure factor is wrong."
    [my_test_configuration,my_test_configuration_universe] = ar4_version0
    value = calculate_sf_fcc_order_parameter(my_test_configuration_universe,
                                             my_test_configuration.wave_vectors,
                                             my_test_configuration.cutoff)
    assert value == 0.01

def test_lop_fcc_exp_terms(ar4_version0):
    [my_test_configuration,my_test_configuration_universe] = ar4_version0

    atom_pairs_indices = my_test_configuration.atom_pairs
    atom_pairs_vectors = my_test_configuration.atom_pairs_vectors
    reference_atom_pairs_exp_terms = my_test_configuration.atom_pairs_exp_terms
    reference_atom_accum_exp_terms = my_test_configuration.atom_accum_exp_terms

    wave_vectors = my_test_configuration.wave_vectors
    n_atoms = my_test_configuration_universe.atoms.n_atoms

    final_accum_exp_terms = ArrayAccumulator(dtype=np.complex64, 
                                capacity=n_atoms,
                                initial_value=0.00,
                                name="Final Accumulated Exp Terms")
    print(f"reference atom pairs exp terms={reference_atom_pairs_exp_terms}")
    print(f"reference atom accum exp terms={reference_atom_accum_exp_terms}")
    for counter in range(len(atom_pairs_indices)):
        key = create_atom_pair_key(*atom_pairs_indices[counter,:])
        (lop_nm_neighbors,exp_terms) = calculate_lop_fcc_exp_terms(
            atom_pairs_indices[counter:counter+1,:],
            atom_pairs_vectors[counter:counter+1,:],
            wave_vectors,n_atoms)


        print(f"Atom pair key: {key}")
        print(f"experimental lop_nm_neighbors: {lop_nm_neighbors}")
        print(f"experimental exp_terms: {exp_terms}")
        print(f"reference exp_terms: {reference_atom_accum_exp_terms}")
        final_accum_exp_terms = merge_array_accumulators(final_accum_exp_terms,
                                                         exp_terms,name="Final Accumulated Exp Terms")
    print(f"Final accumulated exp terms: {final_accum_exp_terms}")
