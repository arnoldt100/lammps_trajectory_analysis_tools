#! /usr/bin/env python3

# Python standard library imports
import json
import os
from pathlib import Path

# Third party library imports
import h5py
import MDAnalysis as mda
import numpy as np
import pytest

# Local Library package imports
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc import (
    LopSfFcc,
    _backend_run_arguments,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
    CLILopSfFcc,
)
from tests.input_files.Ar4Version0 import Ar4Version0

NM_FRAMES = 4
EXAMPLE_DIR = Path(os.environ["LTAT_TOP_LEVEL"]) / "examples" / "example-lop_sf_fcc-ar_box_small"


@pytest.fixture
def run_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """ A directory holding a small Ar4 DCD and simulation-parameter JSON files. """
    structure = Ar4Version0()
    universe = structure.create_md_analysis_universe()
    rng = np.random.default_rng(42)
    with mda.Writer(str(tmp_path / "ar4.dcd"), n_atoms=structure.nm_atoms) as writer:
        for _ in range(NM_FRAMES):
            universe.atoms.positions = (
                structure.coordinates + rng.normal(scale=0.01, size=structure.coordinates.shape))
            writer.write(universe.atoms)

    md_params = json.loads((EXAMPLE_DIR / "md_params.json").read_text())
    md_params["simulation_parameters"]["simulation_metadata"] = str(
        EXAMPLE_DIR / "md_params_metadata.json")
    md_params["simulation_parameters"]["time"]["total_steps"] = NM_FRAMES
    (tmp_path / "md_params.json").write_text(json.dumps(md_params))

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LTAT_DEBUG_PLOT_FRAMES", raising=False)
    return tmp_path


def _run_lop_sf_fcc(run_directory: Path, parallel_threads: int) -> Path:
    structure = Ar4Version0()
    output = run_directory / f"workers_{parallel_threads}.hdf5"
    arguments = CLILopSfFcc(subcommand_name="lop_sf_fcc",
                            trajectory=str(run_directory / "ar4.dcd"),
                            psf=structure.psf_filepath,
                            edge_length=float(structure.lattice_edge_length),
                            timeunits="ps",
                            dt=1.0,
                            cutoff=float(structure.cutoff),
                            output_hdf5_file=str(output),
                            parallel_threads=parallel_threads,
                            md_params_json="md_params.json")
    LopSfFcc()(arguments)
    return output


def _read_datasets(file_path: Path) -> dict[str, np.ndarray]:
    datasets = {}
    with h5py.File(file_path, "r") as output:
        output.visititems(lambda name, item: datasets.__setitem__(name, item[...])
                          if isinstance(item, h5py.Dataset) else None)
    return datasets


def test_parallel_threads_produce_identical_hdf5(run_directory: Path) -> None:
    serial = _read_datasets(_run_lop_sf_fcc(run_directory, parallel_threads=1))
    parallel = _read_datasets(_run_lop_sf_fcc(run_directory, parallel_threads=2))

    assert serial.keys() == parallel.keys()
    written = [name for name in serial if name.endswith("lop_sf_fcc") and serial[name].size]
    assert len(written) == NM_FRAMES
    for name, values in serial.items():
        np.testing.assert_array_equal(parallel[name], values, err_msg=name)


def test_one_thread_runs_serially() -> None:
    assert _backend_run_arguments(1) == {"backend": "serial"}


def test_several_threads_run_multiprocessing_workers() -> None:
    assert _backend_run_arguments(2) == {"backend": "multiprocessing", "n_workers": 2}


def test_more_threads_than_cpus_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 2)
    with pytest.warns(RuntimeWarning):
        assert _backend_run_arguments(3) == {"backend": "multiprocessing", "n_workers": 3}
