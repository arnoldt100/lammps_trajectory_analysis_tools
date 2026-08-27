from typing import Any

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    BuilderRegistry)

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
     lop_sf_fcc_subcommand_name,
     LopSfFccSubparserBuilder,
     process_lop_sf_fcc_cli_args)

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_builder import ( 
    lop_sf_fcc_builder_key,
    LopSfFccBuilder)

analysis_tool_builder_registry: BuilderRegistry[Any] = BuilderRegistry()
analysis_tool_builder_registry.register_builder(lop_sf_fcc_builder_key,
                                                 LopSfFccBuilder())

subparser_builder_registry: BuilderRegistry[Any] = BuilderRegistry()
subparser_builder_registry.register_builder(lop_sf_fcc_subcommand_name(),
        LopSfFccSubparserBuilder())


__all__ = ["subparser_builder_registry",
           "lop_sf_fcc_subcommand_name",
           "analysis_tool_builder_registry",
           "lop_sf_fcc_builder_key"]
