#! /usr/bin/env python3
"""Custom exceptions for the MDAnalysis integration layer."""


class MDAnalysisIntegrationError(Exception):
    """Base exception for MDAnalysis integration failures."""


class UniverseLoadError(MDAnalysisIntegrationError):
    """Raised when an MDAnalysis Universe cannot be created."""


class BridgeValidationError(MDAnalysisIntegrationError):
    """Raised when bridge inputs are invalid for analysis."""


class AnalysisBridgeExecutionError(MDAnalysisIntegrationError):
    """Raised when delegated core analysis execution fails."""
