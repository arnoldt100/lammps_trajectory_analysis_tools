"""Opt-in integration test: a real headless VisIt render.

This test launches a real VisIt subprocess (an external, non-hermetic GUI
renderer) and so is **disabled unless explicitly requested**. Enable it by
setting ``LTAT_RUN_VISIT_INTEGRATION=1`` in the environment; otherwise it is
skipped regardless of whether VisIt is installed. It additionally requires a
resolvable VisIt installation and the small validated argon example.
"""

import os
from pathlib import Path

import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter import (
    LopSfFccVisitPlotter,
    VisitEnvironmentError,
    locate_visit_installation,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLE = (
    _REPO_ROOT
    / "examples"
    / "example-lop_sf_fcc-ar_box_small"
    / "ar_box_small.lop_sf_fcc.nm-frames-1.validated.hdf5"
)

_ENABLED_ENV_VAR = "LTAT_RUN_VISIT_INTEGRATION"


def _visit_available() -> bool:
    try:
        locate_visit_installation()
    except VisitEnvironmentError:
        return False
    return True


@pytest.mark.skipif(
    os.environ.get(_ENABLED_ENV_VAR) != "1",
    reason=f"opt-in only; set {_ENABLED_ENV_VAR}=1 to run",
)
@pytest.mark.skipif(
    not _visit_available(), reason="VisIt is not installed/resolvable"
)
@pytest.mark.skipif(not _EXAMPLE.is_file(), reason="argon example not present")
def test_headless_render_produces_a_frame(tmp_path: Path) -> None:
    plotter = LopSfFccVisitPlotter(locate_visit_installation(), timeout=180.0)
    frames = plotter.render(_EXAMPLE, tmp_path / "out")

    assert len(frames) == 1
    assert frames[0].suffix == ".png"
    assert frames[0].stat().st_size > 1000
