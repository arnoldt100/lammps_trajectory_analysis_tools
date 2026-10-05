from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter import (
    lop_sf_fcc_visit_plotter_factory,
    LopSfFccVisitPlotterBuilderKey,
    VisitInstallationBuilderKey,
)

EXPECTED_KEYS = frozenset(
    {VisitInstallationBuilderKey, LopSfFccVisitPlotterBuilderKey}
)


def test_the_factory_registers_exactly_the_documented_keys() -> None:
    assert lop_sf_fcc_visit_plotter_factory.keys() == EXPECTED_KEYS


def test_the_plotter_builder_is_registered_and_callable() -> None:
    builder = lop_sf_fcc_visit_plotter_factory
    assert LopSfFccVisitPlotterBuilderKey in builder.keys()
    assert VisitInstallationBuilderKey in builder.keys()
