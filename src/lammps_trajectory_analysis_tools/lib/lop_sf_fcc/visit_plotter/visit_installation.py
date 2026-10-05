#! /usr/bin/env python3
"""Locate and validate the headless VisIt installation.

This module provides the following public members:
    VisitInstallation: An immutable value describing a usable VisIt launcher.
    LTAT_VISIT_ENV_VAR: Environment variable overriding the launcher path.
    DEFAULT_VISIT_SUBPATH: The launcher path relative to ``$AT_SW_PACKAGES``.
    EXTRA_LIBRARY_SUBDIRS: Extra library directories prepended to
        ``LD_LIBRARY_PATH`` so VisIt's bundled components resolve their
        dependencies (for example ``libxml2.so.2``).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.plotter_exceptions import (
    VisitEnvironmentError,
)

# ----------
# Public members
# ----------

"""Environment variable that overrides the VisIt launcher path."""
LTAT_VISIT_ENV_VAR = "LTAT_VISIT"

"""Launcher path relative to ``$AT_SW_PACKAGES`` when no override is given."""
DEFAULT_VISIT_SUBPATH = Path("visit") / "bin" / "visit"

"""Extra library directories (relative to ``$AT_SW_PACKAGES``) prepended to
``LD_LIBRARY_PATH`` so VisIt's bundled ``mdserver``/``viewer`` resolve their
shared-library dependencies (e.g. ``libxml2.so.2``)."""
EXTRA_LIBRARY_SUBDIRS = (Path("pymol") / "lib",)

"""Environment variables that must be removed from the VisIt subprocess
environment because VisIt's bundled Python rejects them."""
_STRIPPED_ENV_VARS = ("PYTHON_GIL",)


class VisitInstallation:
    """Describe a usable headless VisIt launcher.

    The value is immutable: attributes are read-only and stored privately.
    """

    __slots__ = ("_launcher", "_extra_library_dirs")

    def __init__(
        self,
        launcher: str | Path,
        extra_library_dirs: tuple[Path, ...] = (),
    ) -> None:
        """Initialize the installation value.

        Args:
            launcher: Path to the VisIt launcher executable.
            extra_library_dirs: Directories prepended to ``LD_LIBRARY_PATH``
                for the VisIt subprocess.

        Raises:
            VisitEnvironmentError: If the launcher does not exist or is not
                executable.
        """
        launcher_path = Path(launcher)
        if not launcher_path.is_file() or not os.access(launcher_path, os.X_OK):
            raise VisitEnvironmentError(
                f"VisIt launcher not found or not executable: '{launcher_path}'"
            )
        self._launcher = launcher_path
        self._extra_library_dirs = tuple(Path(d) for d in extra_library_dirs)

    @property
    def launcher(self) -> Path:
        """Return the VisIt launcher path."""
        return self._launcher

    @property
    def extra_library_dirs(self) -> tuple[Path, ...]:
        """Return the directories prepended to ``LD_LIBRARY_PATH``."""
        return self._extra_library_dirs

    def subprocess_environment(
        self, base: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Return a subprocess environment for VisIt.

        Free-threaded flags such as ``PYTHON_GIL`` are stripped (VisIt's
        bundled Python rejects them), and the extra library directories are
        prepended to ``LD_LIBRARY_PATH``.

        Args:
            base: Environment to start from; defaults to ``os.environ``.

        Returns:
            A new environment mapping safe for the VisIt subprocess.
        """
        env = dict(os.environ if base is None else base)
        for name in _STRIPPED_ENV_VARS:
            env.pop(name, None)
        extra = [str(d) for d in self._extra_library_dirs if d.is_dir()]
        existing = env.get("LD_LIBRARY_PATH")
        if extra:
            env["LD_LIBRARY_PATH"] = (
                os.pathsep.join(extra + [existing]) if existing else os.pathsep.join(extra)
            )
        return env

    def __eq__(self, other: object) -> bool:
        """Compare by launcher and extra library directories."""
        if not isinstance(other, VisitInstallation):
            return NotImplemented
        return (
            self._launcher == other._launcher
            and self._extra_library_dirs == other._extra_library_dirs
        )

    def __repr__(self) -> str:
        """Return a debugging representation."""
        return (
            f"VisitInstallation(launcher={str(self._launcher)!r}, "
            f"extra_library_dirs={self._extra_library_dirs!r})"
        )

    def __hash__(self) -> int:
        """Hash by launcher and extra library directories."""
        return hash((self._launcher, self._extra_library_dirs))


def locate_visit_installation(
    launcher: str | Path | None = None,
    environ: dict[str, str] | None = None,
) -> VisitInstallation:
    """Locate the VisIt launcher and build an installation value.

    Resolution order:

    1. an explicit ``launcher`` argument;
    2. the ``LTAT_VISIT`` environment variable;
    3. ``$AT_SW_PACKAGES/visit/current/bin/visit``.

    Args:
        launcher: Explicit launcher path, or ``None`` to resolve from the
            environment.
        environ: Environment to read; defaults to ``os.environ``.

    Returns:
        A validated ``VisitInstallation``.

    Raises:
        VisitEnvironmentError: If no launcher can be located or it is not
            usable.
    """
    env = os.environ if environ is None else environ

    candidate: str | None = None
    if launcher is not None:
        candidate = str(launcher)
    elif env.get(LTAT_VISIT_ENV_VAR):
        candidate = env[LTAT_VISIT_ENV_VAR]
    else:
        sw_packages = env.get("AT_SW_PACKAGES")
        if not sw_packages:
            raise VisitEnvironmentError(
                "could not locate VisIt: set "
                f"{LTAT_VISIT_ENV_VAR} or AT_SW_PACKAGES"
            )
        candidate = str(Path(sw_packages) / DEFAULT_VISIT_SUBPATH)

    extra_dirs: tuple[Path, ...] = ()
    sw_packages = env.get("AT_SW_PACKAGES")
    if sw_packages:
        extra_dirs = tuple(
            Path(sw_packages) / sub for sub in EXTRA_LIBRARY_SUBDIRS
        )

    return VisitInstallation(candidate, extra_library_dirs=extra_dirs)


def probe_visit_version(
    installation: VisitInstallation,
    environ: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> str:
    """Return the VisIt version string via a headless CLI probe.

    Uses ``visit -cli -nowin -version``; the bare launcher must never be run
    without ``-nowin`` because that launches the GUI.

    Args:
        installation: The located VisIt installation.
        environ: Environment to start from; defaults to ``os.environ``.
        timeout: Seconds to wait for the probe.

    Returns:
        The version string reported by VisIt.

    Raises:
        VisitEnvironmentError: If the probe fails or reports no version.
    """
    env = installation.subprocess_environment(environ)
    command = [str(installation.launcher), "-cli", "-nowin", "-version"]
    try:
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise VisitEnvironmentError(
            f"could not run VisIt probe '{' '.join(command)}'"
        ) from error

    output = f"{result.stdout}\n{result.stderr}"
    for line in output.splitlines():
        line = line.strip()
        if "version of VisIt is" in line:
            return line.rsplit(" ", 1)[-1].strip(".")
    raise VisitEnvironmentError(
        "VisIt probe did not report a version "
        f"(exit {result.returncode}): {output.strip()!r}"
    )


# ----------
# Private members
# ----------


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
