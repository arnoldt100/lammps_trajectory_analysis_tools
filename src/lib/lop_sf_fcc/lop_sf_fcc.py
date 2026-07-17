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
from MDAnalysis.lib.nsgrid import FastNS

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

def create_primitive_wavevectors1():
    # We define the primitive lattice vectors for an edge length of 1.0
    # angstroms.
    a1 = np.array([0,1,1], dtype=np.float64)
    b1 = np.array([1,0,1], dtype=np.float64)
    c1 = np.array([1,1,0], dtype=np.float64)

    # We define the primitive lattice volume for an edge length of 1.0
    # angstroms. We need the primitive lattice volume to later define
    # the reciprocal lattice vectors.
    primitive_lattice_volume1 = np.dot(a1,np.cross(b1,c1))

    # We define the reciprocal lattice vectors for primitive_lattice_vectors1.
    k_a1 = np.cross(b1,c1)
    k_b1 = np.cross(c1,a1)
    k_c1 = np.cross(a1,b1)
    reciprocal_lattice_vectors1 = (
            (2.0*np.pi/primitive_lattice_volume1)*np.array([k_a1,k_b1,k_c1],dtype=np.float64))

    # We define the wavevectors that correspond to primitive_lattice_vectors1.
    wv1_0 = reciprocal_lattice_vectors1[1] + reciprocal_lattice_vectors1[2]
    wv1_1 = reciprocal_lattice_vectors1[0] + reciprocal_lattice_vectors1[2]
    wv1_2 = reciprocal_lattice_vectors1[0] + reciprocal_lattice_vectors1[1]
    wv1_3 = wv1_0 + wv1_1
    wv1_4 = wv1_0 - wv1_1
    wv1_5 = wv1_1 + wv1_2
    wavevectors1 = np.array([wv1_0,wv1_1,wv1_2,wv1_3,wv1_4,wv1_5])
    return wavevectors1

class LopSfFcc:
    """ A callable class that calculates a fcc local order parameter. """

    wavevectors1 = create_primitive_wavevectors1()

    def __init__(self,*args,**kwargs)->None:
        self.__accumulator = []
        self._normalized_wave_vectors = None
        return

    def __call__(self, command_line_arguments:CLILopSfFcc,
                 *args: Any, **kwargs: Any) -> Any:

        # We get the edge length of the fcc lattice and define
        # reciprocal lattice vectors for this edge length.
        edge_length = command_line_arguments.edge_length


        # --
        # Start of code section is to be removed.
        # --
        # # Set the normalized reciprocal lattice wave vectors.
        # self._normalized_wave_vectors : WaveVectors = (
        #     (2.00/np.pi)*(1.00/command_line_arguments.edge_length)*copy.deepcopy(self.non_normalized_wave_vectors))

        # # Read the DCD trajectory.
        # psf_file = command_line_arguments.psf
        # trajectory = command_line_arguments.trajectory
        # timeunits = command_line_arguments.timeunits
        # dt = command_line_arguments.dt
        # cutoff = command_line_arguments.cutoff

        # universe = (
        #     mda.Universe(psf_file,trajectory,timeunits=timeunits,dt=dt))

        # box = universe.trajectory[0].dimensions
        # print (f"box: {box}")

        # all_atoms = universe.select_atoms("all")

 
        # # Loop over every frame in the dcd trajectory, compute
        # # for every atom the local order parameter. We acccumulate the lop values.
        # for ts in universe.trajectory[:]:
        #     time = universe.trajectory.time
        #     print(f"=== timestep {time} ===\n")
        #     print(f"Position atom[0] = {all_atoms.positions[0]}\\nn")
        #     value = calculate_sf_fcc_order_parameter(all_atoms.positions,
        #                                              self._normalized_wave_vectors,
        #                                              cutoff,
        #                                              box)
        #     break
        # --
        # End of code section is to be removed.
        # --

def calculate_sf_fcc_order_parameter(atom_coordinates: AtomCoordinates,
                                     normalized_wave_vectors: WaveVectors,
                                     cutoff,
                                     box: np.ndarray[tuple[Literal[6]],np.dtype[np.float32]])-> float:
    grid = mda.lib.nsgrid.FastNS(cutoff,atom_coordinates,box=box,pbc=False)
    ns_results = grid.self_search()
    pairs = ns_results.get_pairs()
    distances = ns_results.get_pair_distances()
    print("\n=== Box ===")
    print(box)
    print("\n=== Coordinates ===")
    print(atom_coordinates)
    print("\n=== Pairs ====")
    print(pairs)
    print("\n=== Distances ====")
    print(distances)
    print()
 
 

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

