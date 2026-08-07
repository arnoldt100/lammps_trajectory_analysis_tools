#! /usr/bin/env python3

""" Responsible for the LOP SF FCC comman line arguments.

"""

# Python standard library imports
import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Required,Any

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
    subcommand_name:str = None
    trajectory: str = None
    psf: str = None
    edge_length: float = None
    output: str = None
    timeunits: str = None
    dt: float = None
    cutoff: float = None
    do_data_analysis: Callable[...,None] = None

class LopSfFccSubparserFactory:
    """ The concrete builder for LOP Structure FCC order parameter. 

    This a callable object. When called it adds the subparser
    for LOP Structure FCC order parameter.
    """
    _subcommand_help = ( "The command calculates the local order "
                         "parameter for the fcc structure factor." )

    _trajectory_help = "The lammps dcd file."

    _edgelength_help = "The length in angstroms of the edge of the fcc lattice."

    _ouput_help = "The file to write the results. (default : %(default)s)"

    _psf_help = "The protein structure file for the corresponding dcd file."

    _timeunits_help = "The time step units."

    _dt_help = "The time frame interval."

    _cutoff_help = "The neighbor search cutoff in angstroms."

    def __init__(self, *args, **kwargs)->None:
        return

    def __call__(self, top_level_subparsers,
                 *kargs, **kwargs)->None:

        parser1 = top_level_subparsers.add_parser("lop_sf_fcc",
                                                  help=self._subcommand_help)
        parser1.add_argument("--trajectory",
                             type=str,required=True,help=self._trajectory_help)

        parser1.add_argument("--psf",
                             type=str,required=True,help=self._psf_help)

        parser1.add_argument("--edge-length",
                             type=float,required=True,help=self._edgelength_help)

        parser1.add_argument("--timeunits",
                             type=str,required=True,help=self._timeunits_help,
                             choices=["ps"])

        parser1.add_argument("--dt",
                             type=float,required=True,help=self._dt_help)

        parser1.add_argument("--cutoff",
                             type=float,required=True,help=self._cutoff_help)

        parser1.add_argument("--output",
                             type=str,required=False,
                             default="output.data",help=self._ouput_help)

        # Add the callable object for calculating the local structure factor
        # fcc order parameter as an the callable attribute  'do_data_analysis'.
        from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_builder import key_lop_sf_fcc_factory
        from lammps_trajectory_analysis_tools.lib import lammps_analysis_tool_builder
        my_analysis_tool = (
            lammps_analysis_tool_builder.analysis_tool_factory.create_analysis_tool(key_lop_sf_fcc_factory) )
        parser1.set_defaults(do_data_analysis=my_analysis_tool)

def process_lop_sf_fcc_cli_args(my_arg_parser : argparse.ArgumentParser)->CLILopSfFcc:
    my_cliargs = CLILopSfFcc(**vars(my_arg_parser.parse_args()))
    return my_cliargs


def create_mdanalysis_arguments( cli_lop_fcc: CLILopSfFcc)->tuple[dict[str,Any],dict[str,Any]]:
    """ Create the positional and keyword arguments for MDAnalysis Universe creation.

    Args: 
        cli_lop_fcc: The command line arguments for the lop_sf_fcc subcommand.

    Returns:
        A tuple containing two dictionaries:
            - The first dictionary contains the positional arguments for MDAnalysis Universe creation.
            - The second dictionary contains the keyword arguments for MDAnalysis Universe creation.

    """

    # The positional arguments for MDAnalysis Universe creation are the
    # topology file and the trajectory source. These arguments are required and
    # must be provided by the user.
    my_positional_args = {"topology_path" : cli_lop_fcc.psf,
              "trajectory_source" : cli_lop_fcc.trajectory}
 
    # The keyword arguments for MDAnalysis Universe creation are optional and
    # can be provided by the user.
    my_keyword_args = {}
    # Check for valid timestep in dataclass cli_lop_fcc.
    if hasattr(cli_lop_fcc,"dt") and getattr(cli_lop_fcc,"dt") is not None:
        my_keyword_args = {"dt" : cli_lop_fcc.dt}

    return my_positional_args, my_keyword_args

def _main()->None:
    return

if __name__ == "__main__":
    _main()
