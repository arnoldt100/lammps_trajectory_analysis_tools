#! /usr/bin/env python3

""" Responsible for the LOP SF FCC comman line arguments.

"""

# Python standard library imports
import argparse
from collections.abc import Callable
from dataclasses import dataclass

# Local Library package imports

# ----------
# Public members
# ----------

""" The subcommand name for the command line arguments.

Each subcommand name must be unique.
"""
def lop_sf_fcc_subcommand_name()->str:
    return 'lop_sf_fcc'

@dataclass
class CLILopSfFcc:
    """ Stores the command line arguments for the lop_sf_fcc subcommand. """
    subcommand_name:str
    dcd_file_name: str
    psf: str
    edge_length: str
    output: str
    do_data_analysis: Callable[...,None]

class LopSfFccSubparserFactory:
    """ The concrete builder for LOP Structure FCC order parameter. 

    This a callable object. When called it adds the subparser
    for LOP Structure FCC order parameter.
    """
    _subcommand_help = ( "The command calculates the local order "
                         "parameter for the fcc structure factor." )

    _dcdfilename_help = "The lammps dcd file."

    _edgelength_help = "The length in angstroms of the edge of the fcc lattice."

    _ouput_help = "The file to write the results. (default : %(default)s)"

    _psf_help = "The protein structure file for the corresponding dcd file."

    def __init__(self, *args, **kwargs)->None:
        return

    def __call__(self, top_level_subparsers,
                 *kargs, **kwargs)->None:

        parser1 = top_level_subparsers.add_parser("lop_sf_fcc",
                                                  help=self._subcommand_help)
        parser1.add_argument("--dcd-file-name",
                             type=str,required=True,help=self._dcdfilename_help)

        parser1.add_argument("--psf",
                             type=str,required=True,help=self._psf_help)

        parser1.add_argument("--edge-length",
                             type=float,required=True,help=self._edgelength_help)

        parser1.add_argument("--output",
                             type=str,required=False,
                             default="output.data",help=self._ouput_help)

        # Add the callable object for calculating the local structure factor
        # fcc order parameter as an the callable attribute  'do_data_analysis'.
        from lop_sf.fcc.lop_sf_fcc_builder import key_lop_sf_fcc_factory
        import lammps_analysis_tool_builder
        my_function = (
            lammps_analysis_tool_builder.analysis_tool_factory.create(key_lop_sf_fcc_factory) )
        parser1.set_defaults(do_data_analysis=my_function)

def process_lop_sf_fcc_cli_args(my_arg_parser : argparse.ArgumentParser)->CLILopSfFcc:
    my_cliargs = CLILopSfFcc(**vars(my_arg_parser.parse_args()))
    return my_cliargs


def _main()->None:
    return

if __name__ == "__main__":
    _main()
