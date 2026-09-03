import os
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
    data_writer_factory,
)

FRAME_COUNT = 100
ATOM_COUNT = 10_000
BATCH_SIZE = 10
MEMORY_ALLOWANCE_BYTES = 64 * 1024 * 1024

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        os.environ.get("LTAT_RUN_SLOW_TESTS") != "1",
        reason="set LTAT_RUN_SLOW_TESTS=1 to run the reduced-scale streaming tests",
    ),
]


@pytest.fixture
def scale_value_object(tmp_path: Path):
    return data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=tmp_path / "scale.h5",
        metadata={
            "time_units": 0.002,
            "time_units_label": "ps",
            "number_of_trajectories": 1,
            "generation_date": datetime(2026, 9, 3, tzinfo=timezone.utc),
            "compiler_build_flags": ("-O3",),
            "generating_machine": "nimzoindian",
            "lmod_modules": ("gcc/13.2.0",),
        },
        layout={"number_of_atoms": ATOM_COUNT, "compression": "gzip"},
    )


def stream_batches(writer) -> None:
    generator = np.random.default_rng(11)
    for batch_index in range(FRAME_COUNT // BATCH_SIZE):
        first_step = batch_index * BATCH_SIZE
        steps = np.arange(first_step, first_step + BATCH_SIZE, dtype=np.int64)
        writer.append_trajectory_frames(
            0,
            steps,
            generator.random((BATCH_SIZE, ATOM_COUNT, 3)),
            generator.random((BATCH_SIZE, ATOM_COUNT)),
            np.tile([10.0, 11.0, 12.0], (BATCH_SIZE, 1)),
            np.tile([90.0, 90.0, 90.0], (BATCH_SIZE, 1)),
        )


def test_reduced_scale_streaming_writes_every_frame(scale_value_object) -> None:
    with scale_value_object as writer:
        stream_batches(writer)
        target = writer.state.file_path

    with h5py.File(target, "r") as output:
        group = output["trajectories"]["traj_00000"]
        assert group["positions"].shape == (FRAME_COUNT, ATOM_COUNT, 3)
        assert group["lop_sf_fcc"].shape == (FRAME_COUNT, ATOM_COUNT)
        np.testing.assert_array_equal(
            group["step_number"][...], np.arange(FRAME_COUNT, dtype=np.int64)
        )


def test_streaming_peak_memory_stays_bounded(scale_value_object) -> None:
    tracemalloc.start()
    try:
        with scale_value_object as writer:
            stream_batches(writer)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    batch_bytes = BATCH_SIZE * ATOM_COUNT * 3 * 8
    assert peak < batch_bytes + MEMORY_ALLOWANCE_BYTES
