#! /usr/bin/env python3

"""  This module creates the parsers for the command line arguments.

This module's responsibility is to create the top level parser and the subparsers
for this project. Each analysis tool has a corresponding subparser.

We use a factory or builder pattern where each subparser has a concrete 
builder that adds the appropriates options, help messages, etc. 

"""

# Python standard library imports.
import argparse
from typing import Any
from typing import TypeAlias

# Local library import

# Import all definitions needed for the LOP FCC Structure subcommand.
from lop_sf_fcc_cli_parser import LopSfFccSubparserFactory
from lop_sf_fcc_cli_parser import CLILopSfFcc
from lop_sf_fcc_cli_parser import process_lop_sf_fcc_cli_args
from lop_sf_fcc_cli_parser import lop_sf_fcc_subcommand_name

# ----------
# Public members
# ----------

""" A type alias that is the union of all subcommand command line interface types. """
CLI_ID: TypeAlias = CLILopSfFcc

""" A type alias that is the union of all subparser factories. """
SubparserFactory_ID: TypeAlias = LopSfFccSubparserFactory

def process_command_line_arguments()->CLI_ID:
    """Processes the command line arguments. """

    my_top_level_parser = argparse.ArgumentParser(prog="lammps_analysis_tool_parser",
        description="Calculates various physical properties of LAMMPS simulations")

    my_top_level_subparser = my_top_level_parser.add_subparsers(dest="subcommand_name",help="subcommand help")

    # Instatiate a general subparser factory.
    general_subparser_factory = _GeneralSubparserFactory()

    # Instatiate an empty dict to store functions that
    # processs the subcommand command line arguments.
    parse_subcommand_args = {}

    # ----
    # ---  Do over every subcommand.
    # ----

    (parse_subcommand_args,general_subparser_factory) = (
        _process_subcommand_args(parse_subcommand_args,
                                 my_top_level_subparser,
                                 general_subparser_factory,
                                 _lop_sf_fcc_builder_key,
                                 LopSfFccSubparserFactory,
                                 process_lop_sf_fcc_cli_args) )
    # ----
    # --- End of doing every sucommand 
    # ----

    #
    # Now parse the command line args for the subcommand.
    my_args = my_top_level_parser.parse_args()
    subcommand_name = my_args.subcommand_name
    my_CLIArgs : CLI_ID = parse_subcommand_args[subcommand_name](my_top_level_parser)
    return my_CLIArgs

# ----------
# Private members
# ----------

_lop_sf_fcc_builder_key = lop_sf_fcc_subcommand_name()

def _process_subcommand_args (parse_subcommand_args,
                              my_top_level_subparser,
                              general_subparser_factory,
                              registration_key: str,
                              subparser_factory: SubparserFactory_ID,
                              func_process_cli_args):

    # Register the builder and the function to process the command line arguments
    # for the LOP FCC fcc structure factor.
    general_subparser_factory.register_builder(registration_key,subparser_factory)

    # Invoke the add_subparser method to add the subparser
    # to the top level parser.
    general_subparser_factory.add_subparser(registration_key,my_top_level_subparser)

    parse_subcommand_args[registration_key] = func_process_cli_args
    return (parse_subcommand_args,general_subparser_factory)


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


