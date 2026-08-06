#! /usr/bin/env python3
"""Custom exceptions for the MDAnalysis integration layer."""


class MDAnalysisIntegrationError(Exception):
    """Base exception for MDAnalysis integration failures."""


class UniverseLoadError(MDAnalysisIntegrationError):
    """Raised when an MDAnalysis Universe cannot be created."""
