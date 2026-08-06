#! /usr/bin/env python3

# Third party imports
import numpy as np
import pytest

# Local library imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.analysis_bridge import run_lop_sf_fcc_from_universe
from lammps_trajectory_analysis_tools.integrations.mdanalysis.analysis_bridge import run_lop_sf_fcc_terms_from_universe
from lammps_trajectory_analysis_tools.integrations.mdanalysis.errors import BridgeValidationError
from tests.input_files.Ar4Version0 import Ar4Version0


def test_run_lop_sf_fcc_from_universe_matches_reference_coordinates() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    bridge_coordinates = run_lop_sf_fcc_from_universe(universe)

    assert bridge_coordinates.shape == test_config.coordinates.shape
    np.testing.assert_allclose(bridge_coordinates, test_config.coordinates)


def test_run_lop_sf_fcc_terms_from_universe_matches_reference_terms() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    bridge_terms = run_lop_sf_fcc_terms_from_universe(
        universe,
        test_config.wave_vectors,
        float(test_config.cutoff),
    )

    np.testing.assert_allclose(
        bridge_terms,
        test_config.atom_accum_exp_terms_nocoeffs.finalize(),
        rtol=1e-5,
        atol=1e-8,
        equal_nan=False,
        strict=True,
    )


def test_run_lop_sf_fcc_terms_from_universe_rejects_nonpositive_cutoff() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    with pytest.raises(BridgeValidationError):
        run_lop_sf_fcc_terms_from_universe(universe, test_config.wave_vectors, 0.0)


def test_run_lop_sf_fcc_terms_from_universe_rejects_invalid_wave_vectors() -> None:
    test_config = Ar4Version0()
    universe = test_config.create_md_analysis_universe()

    with pytest.raises(BridgeValidationError):
        run_lop_sf_fcc_terms_from_universe(
            universe,
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
            float(test_config.cutoff),
        )
