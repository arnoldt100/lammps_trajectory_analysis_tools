#! /usr/bin/env python3
"""Atom selection helpers for MDAnalysis-backed workflows."""

from __future__ import annotations

import MDAnalysis as mda


def select_atoms(universe_mda: mda.Universe, selection_query: str) -> mda.AtomGroup:
    """Select atoms from a universe using MDAnalysis selection syntax.

    Args:
        universe_mda: Input MDAnalysis universe.
        selection_query: MDAnalysis atom-selection expression.

    Returns:
        Selected MDAnalysis atom group.
    """
    return universe_mda.select_atoms(selection_query)
