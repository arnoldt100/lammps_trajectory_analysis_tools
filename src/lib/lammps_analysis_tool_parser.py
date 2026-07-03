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
from typing import Any
from typing import TypeAlias

# Local library import

# Import all definitions needed for the LOP FCC Structure subcommand.
from lop_sf_fcc.lop_sf_fcc_cli_parser import LopSfFccSubparserFactory
from lop_sf_fcc.lop_sf_fcc_cli_parser import CLILopSfFcc
from lop_sf_fcc.lop_sf_fcc_cli_parser import process_lop_sf_fcc_cli_args
from lop_sf_fcc.lop_sf_fcc_cli_parser import lop_sf_fcc_subcommand_name

""" Define a type alias that is the union of all subcommand command line interface types. """
CLI_ID: TypeAlias = CLILopSfFcc


class _GeneralSubparserFactory:
    """ The director for adding the subparsers to the top level parser."""
    def __init__(self, *args, **kwargs)->None:
        self._builders = {}

    def register_builder(self, key:str, builder:Any)->None:
        self._builders[key] = builder

    def add_subparser(self, key:str, top_level_subparsers,
                      *args, 
                      **kwargs)->None:
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        my_builder = builder()
        my_builder(top_level_subparsers,*args,**kwargs)

# ----------
# This section adds the subparser for the calculating
# LOP Structure FCC.
# ----------

# Register the concrete builder LopSfFccSuparserFactory.
# Each builder key must unique or the undefined behavoir will occur.
# The buider must be name of the subcommand name specified on the command line.
_lop_sf_fcc_builder_key = lop_sf_fcc_subcommand_name()

def process_command_line_arguments()->CLI_ID:
    """Processes the command line arguments. """

    my_top_level_parser = (
        argparse.ArgumentParser(prog="lammps_analysis_tool_parser",
        description="Calculates various physical properties of LAMMPS simulations"))

    my_subparsers = (
        my_top_level_parser.add_subparsers(dest="subcommand_name",
                                           help="subcommand help"))

    # Instatiate a subparser factory.
    my_subparser_factory = _GeneralSubparserFactory()

    # Register the builder and the function to process the command line arguments
    # for the LOP FCC fcc structure factor.
    my_subparser_factory.register_builder(_lop_sf_fcc_builder_key,
        LopSfFccSubparserFactory)

    parse_subcommand_args = { _lop_sf_fcc_builder_key : process_lop_sf_fcc_cli_args }

    # Invoke the add_subparser method to add the subparser
    # to the top level parser.
    my_subparser_factory.add_subparser(_lop_sf_fcc_builder_key,my_subparsers)

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

