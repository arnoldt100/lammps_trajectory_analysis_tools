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

from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter

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
