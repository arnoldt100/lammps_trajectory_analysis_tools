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
from MDAnalysis.lib.pkdtree import PeriodicKDTree
from MDAnalysis.lib.distances import distance_array
from MDAnalysis.lib.distances import calc_bonds
import numpy as np
import numpy.typing as npt

# Local imports
from lop_sf_fcc.lop_sf_fcc_cli_parser import CLILopSfFcc
from data_types import (AtomCoordinates, AtomDisplacement,
    LatticeVectors, AtomPairs, AtomPairsTerms, Box,
    MDA_Universe)
from accumulator.array_accumulator import ArrayAccumulator

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

        box : An numpy 1d array floats of length 6. This is the box dimensions of
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
        pairs[k,0] and pairs[k,;] are the atomic indices of the pair of atoms.
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
    box_lengths = universe.dimensions[0:3]

    initial_atoms_indices_data = pairs[:,0:1]
    initial_atoms_indices = initial_atoms_indices_data.flatten()
    initial_atoms_group = universe.atoms[initial_atoms_indices]
    initial_atoms_positions = initial_atoms_group.positions

    final_atoms_indices_data = pairs[:,1:2]
    final_atoms_indices = final_atoms_indices_data.flatten()
    final_atoms_group = universe.atoms[final_atoms_indices]
    final_atoms_positions = final_atoms_group.positions

    disp_vectors = final_atoms_positions - initial_atoms_positions 
    pbc_delta = box_lengths*np.round(disp_vectors/box_lengths)
    atom_pair_vectors = disp_vectors - pbc_delta

    return atom_pair_vectors

def calculate_lop_fcc_atom_pair_exp_terms(dr,
                                          wavevectors: LatticeVectors,
                                          accumulator_exp_x: ArrayAccumulator )->np.complex64:
    """
    Calculates the sum of the exp(iq*r) for each wave vector q.


    Args:
        dr : The displacement vector 
        wavevectors: The wave_vectors to form the dot product with dr. A numpy
        array of shape (N,3) where wavevectors[i,:] is the i'th wave vector.

    Returns: 
        A complex number
    """
    value = np.complex64(0.00)
    for row_id, row in enumerate(wavevectors):
        x = 1j*np.dot(row,dr)
        exp_x = np.exp(x)
        accumulator_exp_x.accumulate(row_id,exp_x)
        value += exp_x
    return value


def calculate_lop_fcc_exp_terms(atom_pairs_indices,
                                atoms_pairs_vector,
                                wavevectors: LatticeVectors,
                                n_atoms: np.int32):

    """ Calculates the exp(iq*dr) for all wavevectors for all atom pairs in
    atom_pairs_indices.

    Args:
        atoms_pairs_vector: The displacement vector dr from atom 1 to atom 2.

        atom_pairs_indices: The index of the initial atom, atom 1.

        wavevectors: The wave_vectors to form the dot product with dr. A numpy
        array of shape (N,3) where wavevectors[i,:] is the i'th wave vector.

        n_atoms : The total number of atoms in the MDAnalysis universe

    Returns:
        accumulator_atom_nm_neighbors: An ArrayAccumulator that contains the
        number of neighbors for each atom.

        accumulator_atom_exp_terms: An ArrayAccumulator that contains the
        accumulated exp(iq*dr) terms for each atom.
    """
    (nm_pairs,_) = atom_pairs_indices.shape
    (nm_wavevectors,_) = wavevectors.shape

    accumulator_atom_exp_terms = (
        ArrayAccumulator(dtype=np.complex64,capacity=n_atoms,
                         initial_value=np.complex64(0.00),
                         name="atom_exp_accumulator"))

    accumulator_atom_nm_neighbors = (
        ArrayAccumulator(dtype=np.int32,capacity=n_atoms,
                         initial_value=np.int32(0),
                         name="atom_neighbor_accumulator"))

    accumulator_exp_x = (
        ArrayAccumulator(dtype=np.complex64,capacity=nm_wavevectors,
                         initial_value=np.complex64(0.00),
                         name="wavevector_exp_accumulator"))

    for counter1 in range(nm_pairs):
        [atom_index1,atom_index2] = atom_pairs_indices[counter1]
        accumulator_atom_nm_neighbors.accumulate(atom_index1,1)
        accumulator_atom_nm_neighbors.accumulate(atom_index2,1)

        dr = atoms_pairs_vector[counter1]
        accum_exp_iqr_term = calculate_lop_fcc_atom_pair_exp_terms(dr,wavevectors,accumulator_exp_x)
        accumulator_atom_exp_terms.accumulate(atom_index1,accum_exp_iqr_term)
        accumulator_atom_exp_terms.accumulate(atom_index2,accum_exp_iqr_term)
    return (accumulator_atom_nm_neighbors,accumulator_atom_exp_terms)

def calculate_sf_fcc_atom_order_parameter_with_coeffs(nm_atoms: np.int32,
        nm_wavevectors: np.int32,
        accum_lop_terms_no_coeffs: np.ndarray[tuple[int],np.dtype[np.complex64]],
        accum_lop_nm_neighbors: np.ndarray[tuple[int],np.dtype[np.int32]])->np.ndarray[tuple[int],np.dtype[np.float64]]:
    """ Calculates the FCC local order parameter exp(iq*r) for a set of atom
    coordinates.

    These terms factor in the coefficients.


    Args:
        nm_atoms: The number of atoms in the molecular system.
        nm_wavevectors: The number of wave vectors.
        accum_lop_terms_no_coeffs: The struture factor terms for each atom.
        accum_lop_nm_neighbors: The number of neighbors atoms in calculating the structure factor.

    Returns:
        accum_lop_terms_with_coeffs: The struture factor terms for each atom
        adjusted for coefficients.

    """
    accum_lop_terms_with_coeffs = np.zeros(nm_atoms,dtype=np.complex64)
    for atom_index in range(nm_atoms):
        x = np.complex64(0.00)
        if accum_lop_nm_neighbors[atom_index] > 0:
            x = accum_lop_terms_no_coeffs[atom_index]/(nm_wavevectors*accum_lop_nm_neighbors[atom_index])
            y = np.abs(x)**2
            accum_lop_terms_with_coeffs[atom_index] = y
    return accum_lop_terms_with_coeffs

def calculate_sf_fcc_atom_order_parameter_no_coeffs(universe : MDA_Universe,
                                     wave_vectors: LatticeVectors,
                                     cutoff: float)->np.ndarray:
    """ Calculates the FCC local order parameter exp(iq*r) for a set of atom
    coordinates.

    These terms do not factor in any coefficients.

    Args:
        universe: The MDAnalysis universe that contains all the atoms.

        wave_vectors: An numpy array of floats with array shape (N,3) where N
        is the number of wave vectors. The The [i,:] slice is the i'th
        wavevector.

        cutoff: The cutoff to search for neighboring atoms.

    Returns:
        TBD
    """

    ar_atoms = universe.select_atoms("all")
    atom_coordinates = ar_atoms.positions
    box = universe.dimensions
    pairs = calculate_atom_pairs(atom_coordinates,cutoff,box)
    atom_pairs_vectors = calculate_atom_pairs_vectors(universe,pairs)

    # Create an accumulator over for each atom. For each atom we accumulate 
    # the number of neighbors and the exp(q*r) terms.
    nm_atoms = universe.atoms.n_atoms
    (nm_wavevectors,_) = wave_vectors.shape
    accum_lop = np.zeros(nm_atoms,dtype=np.complex64)
    accum_lop_terms = np.zeros(nm_atoms,dtype=np.complex64)
    accum_lop_nm_neighbors = np.zeros(nm_atoms,dtype=np.int64)
 
    (nm_pairs,_) = pairs.shape
    for counter in range(nm_pairs):
        accumulator_exp_x = (
            ArrayAccumulator(dtype=np.complex64,
                             capacity=np.int32(nm_wavevectors),
                             initial_value=np.complex64(0.00),
                             name="wavevector_exp_accumulator"))
        atom_index1 = pairs[counter,0]
        atom_index2 = pairs[counter,1]
        dr = atom_pairs_vectors[counter]
        accum_lop_nm_neighbors[atom_index1] += 1
        accum_lop_nm_neighbors[atom_index2] += 1
        accum1 = calculate_lop_fcc_atom_pair_exp_terms(dr,
                    wave_vectors,
                    accumulator_exp_x)
        accum_lop_terms[atom_index1] += accum1
        accum_lop_terms[atom_index2] += accum1
    return accum_lop_terms

def create_atom_pair_key(atom1: np.int32,
                         atom2: np.int32):
    if atom1 <= atom2:
        key = f"{atom1}-{atom2}"
    else:
        key = f"{atom2}-{atom1}"
    return key

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

        # Form the MDAnalysis universe:wavevectors
# Private members
# ----------

def _create_accumulator():
    """ Returns a accumulator for storing"""
    pass

def _main()->None:
    pass

if __name__ == "__main__":
    _main()

