#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
from typing import Literal, Any

# Third party library imports
import MDAnalysis as mda
from MDAnalysis.lib.nsgrid import FastNS
from MDAnalysis.lib.pkdtree import PeriodicKDTree
from MDAnalysis.lib.distances import distance_array
from MDAnalysis.lib.distances import calc_bonds
import numpy as np
import numpy.typing as npt

# Local imports
from lop_sf_fcc.lop_sf_fcc_cli_parser import CLILopSfFcc
from data_types import AtomCoordinates
from data_types import LatticeVectors
from data_types import AtomPairs
from data_types import Box
from data_types import MDA_Universe

# ----------
# Public members
# ----------

""" A key that is uniquely associated with class LopSfFcc.

This key is used by other classes, especially builder classes, to register the
class LopSfFcc. These callable classes each have a unique key or undefined
behavior may occur. This key is currently not used but reserved for future use.
"""
key_lop_sf_fcc = 'LopSfFcc'

def create_primitive_lattice_vectors(fcc_edge_length : np.float64):
    """ Returns a complex numpy array of shape (3,3).

    Parameters:
        fcc_edge_length : The length in angstroms of the fcc lattice structure
        edge.

    Returns: An numpy array of shape (3,3) where each element is a real
    number. The [i,:] slice is the i'th primitive lattice vector.
    """
    # We define the primitive lattice vectors for an edge length of
    # fcc_edge_length angstroms.
    a = fcc_edge_length*np.array([0,1,1], dtype=np.float64)
    b = fcc_edge_length*np.array([1,0,1], dtype=np.float64)
    c = fcc_edge_length*np.array([1,1,0], dtype=np.float64)

    # We define the primitive_lattice_vectors.
    primitive_lattice_vectors = np.array([a,b,c],dtype=np.float64)
    return primitive_lattice_vectors

def create_reciprocal_lattice_vectors(fcc_edge_length : np.float64):
    """ Returns a complex numpy array of shape (3,3).

    Parameters:
        fcc_edge_length : The length in angstroms of the fcc lattice structure 
                          edge.

    Return:
        An numpy array of shape (3,3) where each element is a real
        number. The [i,:] slice is the i'th reciprocal lattice vector.
    """

    # Define the primitive lattice vectors.
    primitive_lattice_vectors = create_primitive_lattice_vectors(fcc_edge_length)
    a = primitive_lattice_vectors[0,:]
    b = primitive_lattice_vectors[1,:]
    c = primitive_lattice_vectors[2,:]

    # We define the primitive lattice volume for an edge length of 1.0
    # angstroms. We need the primitive lattice volume to later define
    # the reciprocal lattice vectors.
    primitive_lattice_volume = np.dot(a,np.cross(b,c))

    # We define the reciprocal lattice vectors for primitive_lattice_vectors1.
    k_a = np.cross(b,c)
    k_b = np.cross(c,a)
    k_c = np.cross(a,b)
    reciprocal_lattice_vectors = (
            (2.0*np.pi/primitive_lattice_volume)*np.array([k_a,k_b,k_c],dtype=np.float64))
    return reciprocal_lattice_vectors

def create_wavevectors(fcc_edge_length : np.float64):
    """ Returns a complex numpy array of shape (N,3). 

    Parameters:
        fcc_edge_length : The length in angstroms of the fcc lattice structure
        edge.

    Returns: An numpy array of shape (N,3) where each element is a real
    number. The [i,:] slice is the i'th wavevector.
    """

    # We create the reciprocal lattice vectors.
    reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(fcc_edge_length )

    # We define the wavevectors that correspond to various combinations of
    # reciprocal lattice vectors.
    wv_0 = reciprocal_lattice_vectors[1] + reciprocal_lattice_vectors[2]
    wv_1 = reciprocal_lattice_vectors[0] + reciprocal_lattice_vectors[2]
    wv_2 = reciprocal_lattice_vectors[0] + reciprocal_lattice_vectors[1]
    wv_3 = wv_0 + wv_1
    wv_4 = wv_0 - wv_1
    wv_5 = wv_1 + wv_2
    wavevectors = np.array([wv_0,wv_1,wv_2,wv_3,wv_4,wv_5])
    return wavevectors

def calculate_atom_pairs(atom_coordinates: AtomCoordinates,
                         cutoff : float,
                         box: Box)->AtomPairs:
    """ Calculates the atom unique pairs that are within distance 'cutoff'

    The algorithm assumes that we have periodic boundary conditions of a rectangular box.
    Otherwise one may get indeterminate results.

    Args:

        atom_coordinates: The atoms x,y,z atomic coordinates.

        cutoff: The cutoff to search for neighboring atoms.

        box : An numpy 1d array floats of len 6. This is the box dimensions of
        the atomic coordinates in "atom_coordinates" where:
            box_dimensions[0] = x-axis length in angstroms
            box_dimensions[1] = y-axis length in angstroms
            box_dimensions[2] = z-axis length in angstroms
            box_dimensions[3] = Angle between y and z axis in degrees
            box_dimensions[4] = Angle between x and z axis in degrees
            box_dimensions[5] = Angle between x and y axis in degrees

    Returns:
        AtomPairs: An numpy array of integers of shape (N,2). 

        If the variable 'pairs' is returned, then the k'th pair elements
        pairs[k,0] and pairs[k,1] are the atomic indices of the pair of atoms.
        Let i = pairs[k,0], then atom_coordinates[i,:] is coordinates of atom
        corresponding to pairs[k,0]. Similarly, Let j = pairs[k,1], then
        atom_coordinates[j,:] is coordinates of atom corresponding to
        pairs[k,1].
    """

    kdtree = PeriodicKDTree(box=box)
    kdtree.set_coords(atom_coordinates,cutoff)
    pairs = kdtree.search_pairs(cutoff)
    return pairs

def calculate_atom_pairs_vectors(universe : MDA_Universe,
                         pairs: AtomPairs):
    """ Calculates the atom displacement vector between the atoms.

    For each atom pair (i,j), we calculate the vector r_j - r_i.
    The algorithm assumes that we have periodic boundary conditions of a cubic box.
    Otherwise one may get indeterminate results.

    Parameters:

        universe: The MDAnalysis universe that contains all the atoms.

        pairs: The k'th pair, pairs[k,0] and pairs[k,1] are the atomic indices
        of the pair of atoms. Let i = pairs[k,0], then atom_coordinates[i,:] is
        coordinates of atom corresponding to pairs[k,0]. Similarly, Let j =
        pairs[k,1], then atom_coordinates[j,:] is coordinates of atom
        corresponding to pairs[k,1].

 Returns:
        calculate_atom_pairs_vectors

        vector from pairs[k,0] to pairs[k,1].
    """
    print("In function calculate_atom_pairs_vectors")
    [nm_rows,nm_cols] = pairs.shape
    print(f"nm_rows={nm_rows}")
    print(f"nm_cols={nm_cols}")

    box_lengths = universe.dimensions[0:3]
    print(f"box_lenghts={box_lengths}")

    initial_atoms_indices_data = pairs[:,0:1]
    initial_atoms_indices = initial_atoms_indices_data.flatten()
    initial_atoms_group = universe.atoms[initial_atoms_indices]
    initial_atoms_positions = initial_atoms_group.positions

    final_atoms_indices_data = pairs[:,1:2]
    final_atoms_indices = final_atoms_indices_data.flatten()
    final_atoms_group = universe.atoms[final_atoms_indices]
    final_atoms_positions = final_atoms_group.positions

    print(f"initial atom indices={initial_atoms_indices}")
    print(f"initial atom positions={initial_atoms_positions}")
    print(f"final atom indices={final_atoms_indices}")
    print(f"final atom positions={final_atoms_positions}")
    disp_vectors = final_atoms_positions - initial_atoms_positions 
    print(f"disp_vectors = {disp_vectors}")
    atom_pair_vectors = disp_vectors - box_lengths*np.round(disp_vectors / box_lengths)

    print("Leaving function calculate_atom_pairs_vectors")
    return atom_pair_vectors

def calculate_sf_fcc_order_parameter(universe : MDA_Universe,
                                     wave_vectors: LatticeVectors,
                                     cutoff : float)->float:
    """ Calculates the FCC local order parameter for a set of atom coordinates.

    Parameters:
        univers: The MDAnalysis universe that contains all the atoms.

        wave_vectors: An numpy array of floats with array shape (N,3) where N
        is the number of wave vectors. The The [i,:] slice is the i'th
        wavevector.

        cutoff: The cutoff to search for neighboring atoms.
    """

    ar_atoms = universe.select_atoms("all")
    atom_coordinates = ar_atoms.positions
    box = universe.dimensions
    print("\n\n --- PeriodicKDTree --- \n")
    pairs = calculate_atom_pairs(atom_coordinates,cutoff,box)
    print("\n=== Pairs ====")
    print(pairs)
    coords1 = atom_coordinates[pairs[:, 0]]
    coords2 = atom_coordinates[pairs[:, 1]]
    atom_pairs_vectors = calculate_atom_pairs_vectors(universe,pairs)
    print("\n=== Atom Pairs Vectors ====")
    print(atom_pairs_vectors)

    return 0.02

class LopSfFcc:
    """ A callable class that calculates a fcc local order parameter. """


    def __init__(self,*args,**kwargs)->None:
        self.__accumulator = []
        self._normalized_wave_vectors = None
        return

    def __call__(self, command_line_arguments:CLILopSfFcc,
                 *args: Any, **kwargs: Any) -> Any:

        # We get the edge length of the fcc lattice and define
        # reciprocal lattice vectors for this edge length.
        edge_length = np.float64(command_line_arguments.edge_length)
        self.wavevectors = create_wavevectors(edge_length)

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

