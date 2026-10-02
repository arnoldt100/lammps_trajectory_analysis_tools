#! /usr/bin/env python3

# Python standard library imports
from datetime import datetime, timezone
from pathlib import Path

# Third party library imports
import h5py
import MDAnalysis as mda
import numpy as np
import pytest
from MDAnalysis.coordinates.memory import MemoryReader

# Local Library package imports
from lammps_trajectory_analysis_tools.data_writer_utils import (
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    data_writer_factory,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc import lop_sf_fcc_mdanalysis as mdtool
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_mdanalysis import (
    LOP_SF_FCC,
)
from tests.input_files.Ar4Version0 import Ar4Version0

NM_FRAMES = 5


def _ar4_multiframe_universe() -> tuple[mda.Universe, Ar4Version0]:
    structure = Ar4Version0()
    rng = np.random.default_rng(1234)
    coordinates = np.array([
        structure.coordinates + rng.normal(scale=0.01, size=structure.coordinates.shape)
        for _ in range(NM_FRAMES)
    ])
    boxes = np.array([structure.box for _ in range(NM_FRAMES)])
    universe = mda.Universe(structure.psf_filepath,
                            coordinates,
                            format=MemoryReader,
                            dt=structure.timestep,
                            dimensions=boxes)
    return universe, structure


def _perfect_fcc_universe(edge_length: float, nm_cells: int) -> mda.Universe:
    # Conventional cubic cell of side 2*edge_length matches create_primitive_lattice_vectors.
    side = 2.0*edge_length
    basis = np.array([[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=np.float64)*edge_length
    cells = np.array([[i, j, k] for i in range(nm_cells)
                      for j in range(nm_cells)
                      for k in range(nm_cells)], dtype=np.float64)*side
    positions = (cells[:, None, :] + basis[None, :, :]).reshape(-1, 3)
    box_length = side*nm_cells
    universe = mda.Universe.empty(len(positions), trajectory=True)
    universe.atoms.positions = positions
    universe.dimensions = [box_length, box_length, box_length, 90.0, 90.0, 90.0]
    return universe


def test_wavevectors_match_fixture() -> None:
    structure = Ar4Version0()
    np.testing.assert_allclose(mdtool.create_wavevectors(structure.lattice_edge_length),
                               structure.wave_vectors, rtol=1e-5)


@pytest.mark.parametrize("run_kwargs, expected_frames", [
    ({}, list(range(NM_FRAMES))),
    ({"stop": 3}, [0, 1, 2]),
    ({"start": 1, "stop": 5, "step": 2}, [1, 3]),
])
def test_results_shape_and_frames(run_kwargs, expected_frames) -> None:
    universe, structure = _ar4_multiframe_universe()
    analysis = LOP_SF_FCC(universe.atoms, structure.lattice_edge_length,
                          structure.cutoff).run(**run_kwargs)
    n_frames = len(expected_frames)
    assert analysis.results.lop_sf_fcc.shape == (n_frames, structure.nm_atoms)
    assert analysis.results.box_lengths.shape == (n_frames, 3)
    assert analysis.results.box_angles.shape == (n_frames, 3)
    np.testing.assert_array_equal(analysis.frames, expected_frames)


def test_matches_fixture_values() -> None:
    structure = Ar4Version0()
    universe = structure.create_md_analysis_universe()
    analysis = LOP_SF_FCC(universe.atoms, structure.lattice_edge_length,
                          structure.cutoff).run()
    np.testing.assert_allclose(analysis.results.lop_sf_fcc[0],
                               structure.atom_accum_exp_terms_with_coeffs,
                               rtol=1e-5, atol=1e-8)


def test_box_is_stored_per_frame() -> None:
    universe, structure = _ar4_multiframe_universe()
    analysis = LOP_SF_FCC(universe.atoms, structure.lattice_edge_length,
                          structure.cutoff).run()
    for frame_index, ts in enumerate(universe.trajectory):
        np.testing.assert_allclose(analysis.results.box_lengths[frame_index], ts.dimensions[:3])
        np.testing.assert_allclose(analysis.results.box_angles[frame_index], ts.dimensions[3:])


def test_isolated_atom_is_zero() -> None:
    universe, structure = _ar4_multiframe_universe()
    analysis = LOP_SF_FCC(universe.atoms,
                          structure.lattice_edge_length, structure.cutoff).run()
    isolated = np.flatnonzero(structure.accum_lop_nm_neighbors == 0)
    np.testing.assert_array_equal(analysis.results.lop_sf_fcc[:, isolated], 0.0)


def test_perfect_fcc_lattice_is_one() -> None:
    edge_length = 2.5
    universe = _perfect_fcc_universe(edge_length, nm_cells=3)
    cutoff = 1.1*np.sqrt(2.0)*edge_length
    analysis = LOP_SF_FCC(universe.atoms, edge_length, cutoff).run()
    np.testing.assert_allclose(analysis.results.lop_sf_fcc, 1.0, rtol=1e-5)


def test_atomgroup_subset_sizes_results() -> None:
    universe, structure = _ar4_multiframe_universe()
    subset = universe.atoms[[0, 1]]
    analysis = LOP_SF_FCC(subset, structure.lattice_edge_length, structure.cutoff).run()
    assert analysis.results.lop_sf_fcc.shape == (NM_FRAMES, 2)


def test_positions_are_stored_per_frame() -> None:
    universe, structure = _ar4_multiframe_universe()
    analysis = LOP_SF_FCC(universe.atoms, structure.lattice_edge_length,
                          structure.cutoff).run(start=1, step=2)
    assert analysis.results.positions.shape == (2, structure.nm_atoms, 3)
    for row, frame_index in enumerate(analysis.frames):
        universe.trajectory[frame_index]
        np.testing.assert_array_equal(analysis.results.positions[row],
                                      universe.atoms.positions)


def _hdf5_data_writer(file_path: Path, nm_trajectories: int, nm_atoms: int):
    metadata = {
        "time_units_label": "ps",
        "time_step": 1.0,
        "number_of_trajectories": nm_trajectories,
        "generation_date": datetime(2026, 10, 1, tzinfo=timezone.utc),
        "compiler_build_flags": ("-O2",),
        "generating_machine": "test",
        "lmod_modules": ("gcc",),
    }
    layout = {"number_of_atoms": int(nm_atoms), "length_units_label": "A"}
    return data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=file_path,
        metadata=metadata,
        layout=layout,
    )


def _read_trajectories(file_path: Path) -> list[dict[str, np.ndarray]]:
    with h5py.File(file_path, "r") as output:
        root = output["trajectories"]
        return [{name: root[group][name][...] for name in root[group]}
                for group in sorted(root)]


def test_conclude_writes_every_frame_to_the_data_writer(tmp_path: Path) -> None:
    universe, structure = _ar4_multiframe_universe()
    file_path = tmp_path / "lop.hdf5"
    writer = _hdf5_data_writer(file_path, NM_FRAMES, structure.nm_atoms)
    analysis = LOP_SF_FCC(universe.atoms, structure.lattice_edge_length,
                          structure.cutoff, data_writer=writer).run()

    trajectories = _read_trajectories(file_path)
    for row, trajectory in enumerate(trajectories):
        np.testing.assert_array_equal(trajectory["step_number"], [analysis.frames[row]])
        np.testing.assert_allclose(trajectory["lop_sf_fcc"][0], analysis.results.lop_sf_fcc[row])
        np.testing.assert_allclose(trajectory["positions"][0], analysis.results.positions[row])
        np.testing.assert_allclose(trajectory["box_lengths"][0], analysis.results.box_lengths[row])
        np.testing.assert_allclose(trajectory["box_angles"][0], analysis.results.box_angles[row])


def test_later_runs_append_to_the_data_writer(tmp_path: Path) -> None:
    universe, structure = _ar4_multiframe_universe()
    file_path = tmp_path / "lop.hdf5"
    writer = _hdf5_data_writer(file_path, NM_FRAMES, structure.nm_atoms)
    analysis = LOP_SF_FCC(universe.atoms, structure.lattice_edge_length,
                          structure.cutoff, data_writer=writer)
    analysis.run(start=0, stop=2)
    analysis.run(start=2, stop=NM_FRAMES)

    trajectories = _read_trajectories(file_path)
    step_numbers = [int(trajectory["step_number"][0]) for trajectory in trajectories]
    assert step_numbers == list(range(NM_FRAMES))


def test_no_data_writer_writes_nothing(tmp_path: Path) -> None:
    universe, structure = _ar4_multiframe_universe()
    LOP_SF_FCC(universe.atoms, structure.lattice_edge_length, structure.cutoff).run()
    assert list(tmp_path.iterdir()) == []
