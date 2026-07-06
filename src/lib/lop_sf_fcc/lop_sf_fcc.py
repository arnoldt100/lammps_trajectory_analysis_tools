#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
from typing import Any

# Third party library imports
import MDAnalysis as mda
import numpy as np
import numpy.typing as npt

# Local imports
from lop_sf_fcc.lop_sf_fcc_cli_parser import CLILopSfFcc
from data_types import AtomCoordinates
from data_types import AtomCoordinates16
from data_types import AtomCoordinates32
from data_types import AtomCoordinates64

# ----------
# Public members
# ----------

""" A key that is uniquely associated with class LopSfFcc.

This key is used by other classes, especially builder classes, to register the
class LopSfFcc. These callable classes each have a unique key or undefined
behavior may occur. This key is currently not used but reserved for future use.
"""
key_lop_sf_fcc = 'LopSfFcc'

class LopSfFcc:
    """ A callable class that calculates a fcc local order parameter. """
    def __init__(self,*args,**kwargs)->None:
        self.__accumulator = []
        return

    def __call__(self, command_line_arguments:CLILopSfFcc,
                 *args: Any, **kwargs: Any) -> Any:
        psf_file = command_line_arguments.psf
        trajectory = command_line_arguments.trajectory
        timeunits = command_line_arguments.timeunits
        dt = command_line_arguments.dt
        universe = ( 
            mda.Universe(psf_file,trajectory,timeunits=timeunits,dt=dt))

        print(universe)
        print(len(universe.trajectory))

        # Loop over every frame in the dcd trajectory, compute
        # for every atom the local order parameter. We acccumulate the lop values.
        all_atoms = universe.select_atoms("all")
        for ts in universe.trajectory[:]:
            time = universe.trajectory.time
            print(f"--- Frame: {ts.frame:3d}, Time: {time:6.0f} ps ---")
            value = calculate_sf_fcc_order_parameter(all_atoms)
            # Prints a NumPy array of shape (N, 3) containing X, Y, Z coordinates
            print(all_atoms.positions)
            print()
            print()

def calculate_sf_fcc_order_parameter(atom_coordinates: AtomCoordinates)-> float:
    return 0.000

# ----------
# Private members
# ----------

def _create_accumulator():
    """ Returns a accumulator for storing"""
    pass

def _main()->None:
    pass

if __name__ == "__main__":
    _main()

