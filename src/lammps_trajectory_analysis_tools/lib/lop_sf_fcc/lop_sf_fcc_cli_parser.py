#! /usr/bin/env python3

""" Responsible for the LOP SF FCC comman line arguments.

"""

# Python standard library imports
import argparse
from typing import Any, Callable, Optional

# Local Library package imports

# ----------
# Public members
# ----------

""" The subcommand name for the command line arguments.

Each subcommand name must be unique.
"""
def lop_sf_fcc_subcommand_name()->str:
    return 'lop_sf_fcc'

def positive_integer(value: str) -> int:
    """Parse a strictly positive integer command-line value."""
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "parallel thread count must be a positive integer"
        ) from error
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "parallel thread count must be a positive integer"
        )
    return parsed_value

def non_blank_string(value: str) -> str:
    """Parse a string to no leading or trailing whitespaces. """
    if not isinstance(value,str):
        raise argparse.ArgumentTypeError("value must be a string.")

    parsed_value = value.strip()
    if len(parsed_value) == 0:
        raise argparse.ArgumentTypeError("string value must have a positve length.")
    return parsed_value 

class CLILopSfFcc:
    """ Stores the command line arguments for the lop_sf_fcc subcommand. """

    def __init__(
        self,
        subcommand_name: Optional[str] = None,
        trajectory: Optional[str] = None,
        psf: Optional[str] = None,
        edge_length: Optional[float] = None,
        output: Optional[str] = None,
        timeunits: Optional[str] = None,
        dt: Optional[float] = None,
        cutoff: Optional[float] = None,
        output_hdf5_file: Optional[str] = None,
        parallel_threads: int = 1,
        do_data_analysis: Optional[Callable[..., None]] = None,
        md_params_json: Optional[str] = None,
    ) -> None:
        # This can be rewritten as composite specification pattern.
        # The set of if then tests will get extended to validate more
        # function arguments.
        if isinstance(parallel_threads, bool) or not isinstance(parallel_threads, int):
            raise TypeError("parallel_threads must be a positive integer")
        if parallel_threads <= 0:
            raise ValueError("parallel_threads must be a positive integer")
        print(f"Error value: {md_params_json}",flush=True)

        if md_params_json is None or md_params_json.strip() == "a":
            raise ValueError("md_params_json can't be None or a empty string.")

        self._subcommand_name = subcommand_name
        self._trajectory = trajectory
        self._psf = psf
        self._edge_length = edge_length
        self._output = output
        self._timeunits = timeunits
        self._dt = dt
        self._cutoff = cutoff
        self._output_hdf5_file = output_hdf5_file
        self._parallel_threads = parallel_threads
        self._do_data_analysis = do_data_analysis
        self._md_params_json = md_params_json

    @property
    def subcommand_name(self) -> Optional[str]:
        """Return the selected subcommand name."""
        return self._subcommand_name

    @property
    def trajectory(self) -> Optional[str]:
        """Return the trajectory path."""
        return self._trajectory

    @property
    def psf(self) -> Optional[str]:
        """Return the topology path."""
        return self._psf

    @property
    def edge_length(self) -> Optional[float]:
        """Return the FCC edge length."""
        return self._edge_length

    @property
    def output(self) -> Optional[str]:
        """Return the text output path."""
        return self._output

    @property
    def timeunits(self) -> Optional[str]:
        """Return the configured time units."""
        return self._timeunits

    @property
    def dt(self) -> Optional[float]:
        """Return the trajectory timestep."""
        return self._dt

    @property
    def cutoff(self) -> Optional[float]:
        """Return the neighbor-search cutoff."""
        return self._cutoff

    @property
    def output_hdf5_file(self) -> Optional[str]:
        """Return the HDF5 output path."""
        return self._output_hdf5_file

    @property
    def parallel_threads(self) -> int:
        """Return the configured number of parallel threads."""
        return self._parallel_threads

    @property
    def do_data_analysis(self) -> Optional[Callable[..., None]]:
        """Return the configured analysis callable."""
        return self._do_data_analysis

    @property
    def md_params_json(self) -> Optional[str]:
        """ Return the json file name/path that contains the simulation parameters."""
        return self._md_params_json

class LopSfFccSubparserBuilder:
    """ The concrete builder for LOP Structure FCC order parameter . 

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

    _hdf5_data_file_help = "The hdf5 file where the data is stored."

    def __init__(self)->None:
        return

    def __call__(self, top_level_subparsers)->None:

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
                             type=float,
                             required=True,
                             help=self._dt_help)

        parser1.add_argument("--cutoff",
                             type=float,
                             required=True,
                             help=self._cutoff_help)

        parser1.add_argument("--output",
                             type=str,
                             required=False,
                             default="output.data",
                             help=self._ouput_help)

        parser1.add_argument("--output-hdf5-file",
                             type=str,
                             required=False,
                             default="output.hdf5",
                             help=self._hdf5_data_file_help)

        parser1.add_argument("--parallel-threads",
                     type=positive_integer,
                     required=False,
                     default=1,
                     help="Number of parallel threads. If omitted, the default is 1.")

        parser1.add_argument("--md-params-json",
                     type=non_blank_string,
                     required=True,
                     help="The name/file path to a JSON file that contains the simulation parameters.")

        # Add the callable object for calculating the local structure factor
        # fcc order parameter as an the callable attribute  'do_data_analysis'.
        from lammps_trajectory_analysis_tools.lib.lop_sf_fcc import (
            analysis_tool_builder_registry,
            lop_sf_fcc_builder_key,
        )
        my_analysis_tool = analysis_tool_builder_registry.build(lop_sf_fcc_builder_key)
        parser1.set_defaults(do_data_analysis=my_analysis_tool)

def process_lop_sf_fcc_cli_args(my_arg_parser : argparse.ArgumentParser)->CLILopSfFcc:
    my_cliargs = CLILopSfFcc(**vars(my_arg_parser.parse_args()))
    return my_cliargs

def create_mdanalysis_arguments(cli_lop_fcc: CLILopSfFcc)->tuple[dict[str,Any],dict[str,Any]]:
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
