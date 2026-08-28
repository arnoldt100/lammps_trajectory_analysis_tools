#! /usr/bin/env python3

"""  This module creates the parsers for the command line arguments.

This module's responsibility is to create the top level parser and the subparsers
for this project. Each analysis tool has a corresponding subparser and a  
corresponding subcommand.

We use a factory or builder pattern where each subparser/subcommand has a 
concrete builder that adds the appropriates options, help messages, etc. 

The procedure to add a new subparser is demonstrated with the "lop_sf_fcc"
subcommand.


See the section that adds the LOP Structure FCC order parameter as
an example.
"""

import argparse
from typing import TypeAlias

# Local library import
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc import (
    lop_sf_fcc_subcommand_name,
    process_lop_sf_fcc_cli_args,
    subparser_builder_registry,
)

# Import all definitions needed for the LOP FCC Structure subcommand.
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
    CLILopSfFcc,
)

""" Define a type alias that is the union of all subcommand command line interface types. """
type CLI_ID = CLILopSfFcc


# ----------
# This section adds the subparser for the calculating
# LOP Structure FCC.
# ----------
def process_command_line_arguments()->CLI_ID:
    """Processes the command line arguments. """

    my_top_level_parser = (
        argparse.ArgumentParser(prog="lamps_analysis_tool_parser",
        description="Calculates various physical properties of LAMMPS simulations"))

    my_subparsers = (
        my_top_level_parser.add_subparsers(dest="subcommand_name",
                                           help="subcommand help"))

    lop_sf_fcc_builder_key = lop_sf_fcc_subcommand_name()
    parse_subcommand_args = { lop_sf_fcc_builder_key : process_lop_sf_fcc_cli_args }

    # Invoke the add_subparser method to add the subparser
    # to the top level parser.
    subparser_builder_registry.build(lop_sf_fcc_builder_key,my_subparsers)

    # Now parse the command line args for the subcommand.
    my_args = my_top_level_parser.parse_args()
    my_CLIArgs : CLI_ID = parse_subcommand_args[my_args.subcommand_name](my_top_level_parser)

    return my_CLIArgs

# ----------
# End of section that adds the subparser for the calculating
# LOP Structure FCC.
# ----------

# ----------
# Add all additional subparsers below this line.
# ----------

