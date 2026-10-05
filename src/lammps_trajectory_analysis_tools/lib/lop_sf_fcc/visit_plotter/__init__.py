"""VisIt-based time-series plotter for the LOP SF FCC analysis.

This package owns the single ``lop_sf_fcc_visit_plotter_factory`` registry
instance and the one site at which its builders are registered.
"""

from typing import Any

from lammps_trajectory_analysis_tools.design_patterns_templates.builder.builder_registry import (
	BuilderRegistry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.lop_sf_fcc_series_exporter import (
	LopSfFccXdmfExporter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.plotter_exceptions import (
	PlotterConfigurationError,
	PlotterError,
	PlotterRenderError,
	VisitEnvironmentError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_installation import (
	VisitInstallation,
	locate_visit_installation,
	probe_visit_version,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_plotter import (
	LopSfFccVisitPlotter,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_plotter_builder_keys import (
	LopSfFccVisitPlotterBuilderKey,
	VisitInstallationBuilderKey,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_plotter_builders import (
	LopSfFccVisitPlotterBuilder,
	VisitInstallationBuilder,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.visit_render_script import (
	render_script_text,
)

lop_sf_fcc_visit_plotter_factory: BuilderRegistry[Any] = BuilderRegistry()
lop_sf_fcc_visit_plotter_factory.register_builder(
	VisitInstallationBuilderKey,
	VisitInstallationBuilder(),
)
lop_sf_fcc_visit_plotter_factory.register_builder(
	LopSfFccVisitPlotterBuilderKey,
	LopSfFccVisitPlotterBuilder(),
)

__all__ = [
	"LopSfFccVisitPlotter",
	"LopSfFccVisitPlotterBuilder",
	"LopSfFccVisitPlotterBuilderKey",
	"LopSfFccXdmfExporter",
	"PlotterConfigurationError",
	"PlotterError",
	"PlotterRenderError",
	"VisitEnvironmentError",
	"VisitInstallation",
	"VisitInstallationBuilder",
	"VisitInstallationBuilderKey",
	"locate_visit_installation",
	"lop_sf_fcc_visit_plotter_factory",
	"probe_visit_version",
	"render_script_text",
]
