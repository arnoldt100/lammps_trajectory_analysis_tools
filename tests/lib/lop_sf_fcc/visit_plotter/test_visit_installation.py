import os
import stat
from pathlib import Path

import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter import (
    VisitEnvironmentError,
    VisitInstallation,
    locate_visit_installation,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_installation import (
    DEFAULT_VISIT_SUBPATH,
    LTAT_VISIT_ENV_VAR,
)


@pytest.fixture
def executable_launcher(tmp_path: Path) -> Path:
    launcher = tmp_path / "visit"
    launcher.write_text("#! /bin/sh\n")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    return launcher


def test_explicit_launcher_is_used(executable_launcher: Path) -> None:
    installation = locate_visit_installation(launcher=executable_launcher)
    assert installation.launcher == executable_launcher


def test_environment_variable_overrides_default(
    executable_launcher: Path,
) -> None:
    environ = {LTAT_VISIT_ENV_VAR: str(executable_launcher)}
    installation = locate_visit_installation(environ=environ)
    assert installation.launcher == executable_launcher


def test_default_resolution_uses_at_sw_packages(tmp_path: Path) -> None:
    launcher = tmp_path / DEFAULT_VISIT_SUBPATH
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#! /bin/sh\n")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
    environ = {"AT_SW_PACKAGES": str(tmp_path)}
    installation = locate_visit_installation(environ=environ)
    assert installation.launcher == launcher


def test_missing_launcher_raises() -> None:
    with pytest.raises(VisitEnvironmentError):
        locate_visit_installation(launcher="/nonexistent/visit")


def test_no_location_information_raises() -> None:
    with pytest.raises(VisitEnvironmentError):
        locate_visit_installation(environ={})


def test_subprocess_environment_strips_python_gil(
    executable_launcher: Path,
) -> None:
    installation = VisitInstallation(executable_launcher)
    env = installation.subprocess_environment({"PYTHON_GIL": "0", "PATH": "/bin"})
    assert "PYTHON_GIL" not in env
    assert env["PATH"] == "/bin"


def test_subprocess_environment_prepends_extra_library_dirs(
    executable_launcher: Path, tmp_path: Path
) -> None:
    extra = tmp_path / "extra_lib"
    extra.mkdir()
    installation = VisitInstallation(
        executable_launcher, extra_library_dirs=(extra,)
    )
    env = installation.subprocess_environment({"LD_LIBRARY_PATH": "/orig"})
    assert env["LD_LIBRARY_PATH"].split(os.pathsep) == [str(extra), "/orig"]


def test_subprocess_environment_skips_missing_extra_dirs(
    executable_launcher: Path, tmp_path: Path
) -> None:
    missing = tmp_path / "does_not_exist"
    installation = VisitInstallation(
        executable_launcher, extra_library_dirs=(missing,)
    )
    env = installation.subprocess_environment({"LD_LIBRARY_PATH": "/orig"})
    assert env["LD_LIBRARY_PATH"] == "/orig"


def test_installation_value_equality_and_hash(executable_launcher: Path) -> None:
    left = VisitInstallation(executable_launcher)
    right = VisitInstallation(executable_launcher)
    assert left == right
    assert hash(left) == hash(right)
    assert "visit" in repr(left).lower()
