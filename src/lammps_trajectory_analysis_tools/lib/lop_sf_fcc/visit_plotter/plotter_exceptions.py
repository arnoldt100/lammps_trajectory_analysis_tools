#! /usr/bin/env python3
"""Exceptions for the LOP SF FCC VisIt plotter.

This module provides the following public members:
    PlotterError: Base class for all plotter errors.
    PlotterConfigurationError: Invalid plotter or export configuration.
    VisitEnvironmentError: VisIt cannot be located or cannot run.
    PlotterRenderError: The VisIt subprocess failed to render.
"""

# ----------
# Public members
# ----------


class PlotterError(Exception):
    """Base class for all LOP SF FCC plotter errors."""


class PlotterConfigurationError(PlotterError):
    """Raised when the plotter or export configuration is invalid."""


class VisitEnvironmentError(PlotterError):
    """Raised when VisIt cannot be located or cannot run in this environment."""


class PlotterRenderError(PlotterError):
    """Raised when the VisIt subprocess fails to render the time series."""


# ----------
# Private members
# ----------


def _main() -> None:
    return


if __name__ == "__main__":
    _main()
