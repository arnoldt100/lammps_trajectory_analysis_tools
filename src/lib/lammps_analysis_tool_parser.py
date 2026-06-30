#! /usr/bin/env python3

"""  This module creates the parsers for the command line arguments.

This module's responsibility is to create the top level parser and the subparsers
for this project. Each analysis tool has a corresponding subparser.

We use a factory or builder pattern where each subparser has a concrete 
builder that adds the appropriates options, help messages, etc. 

The procedure to add a new suparser do the following:

(1) Create a concrete object that adds the appropriate options for the tool 

(2) Register the 'concrete object' with the general subparser factory. 

(3) Invoke the _GeneralSubparserFactory::add_subparser method to add the
subparser to the top level parser.

See the section that adds the LOP Structure FCC order parameter as
an example.
"""

import argparse
from typing import Any

# Local library import 

""" The top level parser for this package. """
top_level_parser = argparse.ArgumentParser(prog="lammps_analysis_tool_parser",
    description="Calculates various physical properties of LAMMPS simulations")

_subparsers = top_level_parser.add_subparsers(help="subcommand help")

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

# Instatiate a subparser factory.
_subparser_factory = _GeneralSubparserFactory()

# ----------
# This section adds the subparser for the calculating
# LOP Structure FCC.
# ----------


class _LopSfFccSuparserFactory:
    """ The concrete builder for LOP Structure FCC order parameter. 

    This a callable object. When called it adds the subparser
    for LOP Structure FCC order parameter.
    """
    _subcommand_help = ( "The command calculates the local order "
                         "parameter for the fcc structure factor." )

    _dcdfilename_help = "The lammps dcd file."

    _edgelength_help = "The length in angstroms of the edge of the fcc lattice."

    _ouput_help = "The file to write the results. (default : %(default)s)"

    def __init__(self, *args, **kwargs)->None:
        return

    def __call__(self, top_level_subparsers,
                 *kargs, **kwargs)->None:

        parser1 = top_level_subparsers.add_parser("lop_sf_fcc",
                                                  help=self._subcommand_help)
        parser1.add_argument("--dcd-file-name",
                             type=str,required=True,help=self._dcdfilename_help)

        parser1.add_argument("--edge-length",
                             type=float,required=True,help=self._edgelength_help)

        parser1.add_argument("--output",
                             type=str,required=False,
                             default="output.data",help=self._ouput_help)

        # Add the callable object for calculating the local structure factor
        # fcc order parameter as an the callable attribute  'do_data_analysis'.
        from lop_sf_fcc_builder import key_lop_sf_fcc_factory
        import lammps_analysis_tool_builder
        my_function = (
            lammps_analysis_tool_builder.analysis_tool_factory.create(key_lop_sf_fcc_factory) )
        parser1.set_defaults(do_data_analysis=my_function)

# Register the concrete builder _LopSfFccSuparserFactory.
# Each builder key must unique or the undefined behavoir will occur.
_lop_sf_fcc_builder_key = '__lop_sf_fcc__'
_subparser_factory.register_builder(_lop_sf_fcc_builder_key,
                                    _LopSfFccSuparserFactory)

# Invoke the add_subparser method to add the subparser
# to the top level parser.
_subparser_factory.add_subparser(_lop_sf_fcc_builder_key,_subparsers)

# ----------
# End of section that adds the subparser for the calculating
# LOP Structure FCC.
# ----------

# ----------
# Add all additional subparsers below this line.
# ----------

