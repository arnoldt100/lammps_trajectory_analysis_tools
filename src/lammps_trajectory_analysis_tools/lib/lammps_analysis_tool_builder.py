#! /usr/bin/env python3

# Python standard library imports
from typing import Any

# Local library import
from lammps_trajectory_analysis_tools.design_patterns_templates.builder import BuilderRegistry
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_builder import key_lop_sf_fcc_factory
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_builder import LopSfFccFactory

# ----------
# Public members
# ----------

analysis_tool_factory: BuilderRegistry[Any] = BuilderRegistry()
analysis_tool_factory.register_builder(key_lop_sf_fcc_factory, LopSfFccFactory())

# ----------
# Private members
# ----------

def _main()->None:
    pass


if __name__ == "__main__":
    _main ()
