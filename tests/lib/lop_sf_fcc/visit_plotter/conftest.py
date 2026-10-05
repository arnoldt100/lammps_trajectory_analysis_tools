from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.hdf5_writer import (
    lop_sf_fcc_data_writer_factory,
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
)

NM_ATOMS = 6
NM_FRAMES = 3


@pytest.fixture
def metadata_args() -> dict:
    return {
        "time_step": 0.002,
        "time_units_label": "ps",
        "number_of_trajectories": NM_FRAMES,
        "generation_date": datetime(2026, 9, 3, tzinfo=timezone.utc),
        "compiler_build_flags": ("-O3",),
        "generating_machine": "test-host",
        "lmod_modules": ("gcc/13.2.0",),
    }


@pytest.fixture
def layout_args() -> dict:
    return {"number_of_atoms": NM_ATOMS, "length_units_label": "angstrom"}


@pytest.fixture
def lop_hdf5_path(tmp_path: Path, metadata_args: dict, layout_args: dict) -> Path:
    """Build a valid LOP SF FCC HDF5 file with NM_FRAMES one-frame trajectories."""
    target = tmp_path / "lop_sf_fcc.hdf5"
    value_object = lop_sf_fcc_data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=target,
        metadata=metadata_args,
        layout=layout_args,
    )
    with value_object as writer:
        for index in range(NM_FRAMES):
            positions = np.full((1, NM_ATOMS, 3), float(index), dtype=np.float64)
            positions[0, :, 0] = np.arange(NM_ATOMS, dtype=np.float64)
            lop = np.linspace(0.0, 1.0, NM_ATOMS, dtype=np.float64).reshape(1, -1)
            box_lengths = np.array([[10.0, 10.0, 10.0]], dtype=np.float64)
            box_angles = np.array([[90.0, 90.0, 90.0]], dtype=np.float64)
            steps = np.array([index], dtype=np.int64)
            writer.append_trajectory_frames(
                index, steps, positions, lop, box_lengths, box_angles
            )
    return target
