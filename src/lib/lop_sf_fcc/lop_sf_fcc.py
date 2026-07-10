#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
from typing import Any
import copy

# Third party library imports
import MDAnalysis as mda
from mda.lib.NeighborSearch import AtomNeighborSearch

import numpy as np
import numpy.typing as npt

# Local imports
from lop_sf_fcc.lop_sf_fcc_cli_parser import CLILopSfFcc
from data_types import AtomCoordinates
from data_types import WaveVectors

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

    k_0 = np.array([1.00, 0.00, 0.00],dtype=np.float64)
    k_1 = np.array([0.00, 1.00, 0.00],dtype=np.float64)
    k_2 = np.array([0.00, 0.00, 1.00],dtype=np.float64)
    k_3 = np.array([1.00, 1.00, 0.00],dtype=np.float64)
    k_4 = np.array([1.00, -1.00, 0.00],dtype=np.float64)
    k_5 = np.array([0.00, 1.00, 1.00],dtype=np.float64)
    non_normalized_wave_vectors : WaveVectors = (np.array([k_0,k_1,k_2,k_3,k_4,k_5] ,dtype=np.float64))

    def __init__(self,*args,**kwargs)->None:
        self.__accumulator = []
        self._normalized_wave_vectors = None
        return

    def __call__(self, command_line_arguments:CLILopSfFcc,
                 *args: Any, **kwargs: Any) -> Any:

        # Set the normalized reciprocal lattice wave vectors.
        self._normalized_wave_vectors : WaveVectors = (
            (2.00/np.pi)*(1.00/command_line_arguments.edge_length)*copy.deepcopy(self.non_normalized_wave_vectors))

        # Read the DCD trajectory.
        psf_file = command_line_arguments.psf
        trajectory = command_line_arguments.trajectory
        timeunits = command_line_arguments.timeunits
        dt = command_line_arguments.dt
        universe = (
            mda.Universe(psf_file,trajectory,timeunits=timeunits,dt=dt))

        all_atoms = universe.select_atoms("all")

        ns = AtomNeighborSearch(all_atoms,box=universe.dimensions)
 
        # Loop over every frame in the dcd trajectory, compute
        # for every atom the local order parameter. We acccumulate the lop values.
        for ts in universe.trajectory[:]:
            time = universe.trajectory.time
            value = calculate_sf_fcc_order_parameter(all_atoms,
                self._normalized_wave_vectors)

def calculate_sf_fcc_order_parameter(atom_coordinates: AtomCoordinates,
                                     normalized_wave_vectors: WaveVectors )-> float:
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

