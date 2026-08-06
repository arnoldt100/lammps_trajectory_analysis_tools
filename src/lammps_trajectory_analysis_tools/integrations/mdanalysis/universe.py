#! /usr/bin/env python3
"""Universe loader helpers for MDAnalysis-backed workflows."""

from __future__ import annotations

from typing import Any

import MDAnalysis as mda

from lammps_trajectory_analysis_tools.integrations.mdanalysis.errors import UniverseLoadError


def load_universe(topology_path: str, trajectory_source: Any, **kwargs: Any) -> mda.Universe:
    """Create an MDAnalysis Universe from topology and trajectory inputs.

    Args:
        topology_path: Path to the topology file.
        trajectory_source: Path or in-memory trajectory source accepted by
            ``MDAnalysis.Universe``.
        **kwargs: Additional keyword arguments passed to MDAnalysis.Universe.

    Returns:
        The initialized MDAnalysis Universe object.

    Raises:
        UniverseLoadError: If MDAnalysis fails to build the universe.
    """
    try:
        return mda.Universe(topology_path, trajectory_source, **kwargs)
    except Exception as exc:  # pragma: no cover - passthrough wrapper
        raise UniverseLoadError(str(exc)) from exc
