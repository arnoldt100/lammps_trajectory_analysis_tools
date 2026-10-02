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

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_mdanalysis import (
    calculate_sf_fcc_atom_order_parameter_no_coeffs,
    calculate_sf_fcc_atom_order_parameter_with_coeffs)

from lammps_trajectory_analysis_tools.accumulator import (
    array_accumulator_builder_key,
    array_accumulator_builder_registry,
)

@pytest.fixture
def ar4_version0():
    test_configuration = Ar4Version0()
    test_configuration_universe = test_configuration.create_md_analysis_universe()
    return [test_configuration,test_configuration_universe]

def test_lop_sf_fcc_atom_order_parameter_with_coeffs(ar4_version0):
    rtolerance = 1e-5
    atolerance = 1e-8

    [my_test_configuration,my_test_configuration_universe] = ar4_version0

    atom_accum_exp_terms_nocoeffs = my_test_configuration.atom_accum_exp_terms_nocoeffs
    nm_wavevectors = my_test_configuration.nm_wavevectors
    accum_lop_nm_neighbors = my_test_configuration.accum_lop_nm_neighbors
    nm_atoms = my_test_configuration.nm_atoms

    accum_lop_terms_with_coeffs = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.float64,
        capacity=np.int32(nm_atoms),
        initial_value=np.float64(0.00),
        name="atom_exp_terms_accumulator",
    )

    programatic_values = calculate_sf_fcc_atom_order_parameter_with_coeffs(nm_atoms,
                                                                           nm_wavevectors,
                                                                           atom_accum_exp_terms_nocoeffs.finalize(),
                                                                           accum_lop_nm_neighbors,
                                                                           accum_lop_terms_with_coeffs)

    reference_values = my_test_configuration.atom_accum_exp_terms_with_coeffs
    np.testing.assert_allclose(programatic_values.finalize(),
                               reference_values,
                               rtol=rtolerance,
                               atol=atolerance,
                               equal_nan=False,
                               strict=True)

def test_lop_sf_fcc_atom_order_parameter_no_coeffs(ar4_version0):
    rtolerance = 1e-5
    atolerance = 1e-8

    [my_test_configuration,my_test_configuration_universe] = ar4_version0

    n_atoms = my_test_configuration_universe.atoms.n_atoms
    accumulator_nm_neighbors = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.int32,
        capacity=np.int32(n_atoms),
        initial_value=np.int32(0),
        name="atom_neighbor_accumulator",
    )
    accumulator_lop_terms0 = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.complex64,
        capacity=np.int32(n_atoms),
        initial_value=np.complex64(0.00),
        name="atom_exp_terms_accumulator",
    )

    (programatic_values,programatic_nm_neighbors) = (
        calculate_sf_fcc_atom_order_parameter_no_coeffs(my_test_configuration_universe.atoms,
        my_test_configuration.wave_vectors,
        my_test_configuration.cutoff,
        accumulator_nm_neighbors,
        accumulator_lop_terms0) )

    reference_values = my_test_configuration.atom_accum_exp_terms_nocoeffs

    np.testing.assert_allclose(programatic_values,
                               reference_values.finalize(),
                               rtol=rtolerance,
                               atol=atolerance,
                               equal_nan=False,
                               strict=True)


