#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
from typing import Any

# Third party library imports
import numpy as np

# Local imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.universe import (
    calculate_atom_pairs,
    calculate_atom_pairs_vectors,
    load_universe,
)
from lammps_trajectory_analysis_tools.lib.accumulator.array_accumulator import (
    ArrayAccumulator,
)
from lammps_trajectory_analysis_tools.lib.data_types import (
    LatticeVectors,
    MDA_Universe,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
    CLILopSfFcc,
    create_mdanalysis_arguments,
)
from lammps_trajectory_analysis_tools.timer_utils import (
    LoopTimerBuilderKey,
    timer_object_factory,
)

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

        atom_pairs_indices: The index of the initial atom, atom 1.

        atoms_pairs_vector: The displacement vector dr from atom 1 to atom 2.

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
                                     cutoff: float)->tuple[np.ndarray,np.ndarray]:
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
        A tuple of the accumulated exp(q*r) terms and the number of neighbors
        of each atom.
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
    return (accum_lop_terms,accum_lop_nm_neighbors)

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

        # This attribute stores the final FCC structure propert for 
        # each at time t.
        self._lop_sf_fcc = None
        return

    def __call__(self, command_line_arguments:CLILopSfFcc,
                 *args: Any, **kwargs: Any) -> Any:

        # We get the edge length of the fcc lattice and define
        # reciprocal lattice vectors for this edge length.
        edge_length = np.float64(command_line_arguments.edge_length)

        # Form the MDAnalysis universe:wavevectors
        self._wavevectors = create_wavevectors(edge_length)

        # Form the universse .
        my_positional_args,my_keyword_args = create_mdanalysis_arguments(command_line_arguments)
        my_universe = load_universe(my_positional_args["topology_path"],
                                    my_positional_args["trajectory_source"],
                                    **my_keyword_args)

        # Loop over each trajectory and calculate the lop fcc fcc
        nm_frames = my_universe.trajectory.n_frames
        nm_atoms = my_universe.atoms.n_atoms
        nm_wavevectors,_ = self._wavevectors.shape

        print(f"Number of trajectory frames = {nm_frames}")

        report_iteration = 5
        max_trajectories_to_compute = 100
        trajectory_loop_timer = (
            timer_object_factory.build(LoopTimerBuilderKey,"trajectory_loop",max_trajectories_to_compute,report_iteration)
        )
        trajectory_loop_timer.start()
        counter = 0
        for ts in my_universe.trajectory:
            frame_index = ts.frame
            frame_time = ts.time

            (accum_lop_terms0,accum_nm_neighbors) = (
                calculate_sf_fcc_atom_order_parameter_no_coeffs(my_universe,
                    self._wavevectors,
                    np.float32(command_line_arguments.cutoff))
            )

            accum_lop_terms1 = (
                calculate_sf_fcc_atom_order_parameter_with_coeffs(nm_atoms,
                    nm_wavevectors,
                    accum_lop_terms0,
                    accum_nm_neighbors))


            counter += 1
            trajectory_loop_timer.update(counter)

            if counter == max_trajectories_to_compute:
                break
        trajectory_loop_timer.stop()
        return

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

