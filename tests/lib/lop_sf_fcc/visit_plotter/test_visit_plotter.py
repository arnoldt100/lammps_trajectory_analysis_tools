import stat
import subprocess
from pathlib import Path

import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter import (
    LopSfFccVisitPlotter,
    PlotterConfigurationError,
    PlotterRenderError,
    VisitInstallation,
)

from .conftest import NM_FRAMES


@pytest.fixture
def installation(tmp_path: Path) -> VisitInstallation:
    launcher = tmp_path / "visit"
    launcher.write_text("#! /bin/sh\n")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
    return VisitInstallation(launcher)


def test_render_rejects_an_invalid_color_range(
    installation: VisitInstallation, lop_hdf5_path: Path, tmp_path: Path
) -> None:
    plotter = LopSfFccVisitPlotter(installation)
    with pytest.raises(PlotterConfigurationError):
        plotter.render(lop_hdf5_path, tmp_path / "out", color_min=1.0, color_max=0.0)


def test_constructor_rejects_a_non_positive_timeout(
    installation: VisitInstallation,
) -> None:
    with pytest.raises(PlotterConfigurationError):
        LopSfFccVisitPlotter(installation, timeout=0.0)


def test_render_raises_when_the_subprocess_fails(
    installation: VisitInstallation,
    lop_hdf5_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0], returncode=1, stdout="boom", stderr="failed"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    plotter = LopSfFccVisitPlotter(installation)
    with pytest.raises(PlotterRenderError):
        plotter.render(lop_hdf5_path, tmp_path / "out")


def test_render_raises_when_no_frames_are_produced(
    installation: VisitInstallation,
    lop_hdf5_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="NUM_STATES 1\nRENDER_OK", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    plotter = LopSfFccVisitPlotter(installation)
    with pytest.raises(PlotterRenderError):
        plotter.render(lop_hdf5_path, tmp_path / "out")


def test_render_invokes_visit_headless_with_scrubbed_env(
    installation: VisitInstallation,
    lop_hdf5_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}
    out_dir = tmp_path / "out"

    def fake_run(command, env=None, **kwargs):
        captured["command"] = command
        captured["env"] = env
        # Emulate VisIt writing the expected number of frames.
        for index in range(NM_FRAMES):
            (out_dir / f"frame_{index:04d}.png").write_bytes(b"\x89PNG")
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout="RENDER_OK", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("PYTHON_GIL", "0")

    plotter = LopSfFccVisitPlotter(installation)
    frames = plotter.render(lop_hdf5_path, out_dir)

    command = captured["command"]
    assert command[0] == str(installation.launcher)
    assert "-cli" in command and "-nowin" in command and "-s" in command
    assert "PYTHON_GIL" not in captured["env"]
    assert len(frames) == NM_FRAMES
    assert all(f.suffix == ".png" for f in frames)
