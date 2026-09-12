#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
import os
from pathlib import Path
from typing import Any

# Third party library imports
import numpy as np

# Local imports
from lammps_trajectory_analysis_tools.accumulator import (
    array_accumulator_builder_key,
    array_accumulator_builder_registry,
)
from lammps_trajectory_analysis_tools.accumulator.array_accumulator import (
    ArrayAccumulator,
)
from lammps_trajectory_analysis_tools.integrations.mdanalysis.universe import (
    calculate_atom_pairs,
    calculate_atom_pairs_vectors,
    load_universe,
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

from lammps_trajectory_analysis_tools.schemas import (
    read_json_file,
    validate_json_file,
)

from lammps_trajectory_analysis_tools.lib.data_types import JSON

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
        lop_terms_no_coeffs: np.ndarray[tuple[int],np.dtype[np.complex64]],
        lop_nm_neighbors: np.ndarray[tuple[int],np.dtype[np.int32]],
        accum_lop_terms_with_coeffs: ArrayAccumulator)->ArrayAccumulator:
    """ Calculates the FCC local order parameter exp(iq*r) for a set of atom
    coordinates.

    These terms factor in the coefficients.


    Args:
        nm_atoms: The number of atoms in the molecular system.
        nm_wavevectors: The number of wave vectors.
        lop_terms_no_coeffs: The struture factor terms for each atom.
        lop_nm_neighbors: The number of neighbors atoms in calculating the structure factor.
        accum_lop_terms_with_coeffs: The values of lop sf FCC for each atom.

    Returns:
        accum_lop_terms_with_coeffs: The struture factor terms for each atom
        adjusted for coefficients.

    """
    for atom_index in range(nm_atoms):
        x = np.complex64(0.00)
        if lop_nm_neighbors[atom_index] > 0:
            x = lop_terms_no_coeffs[atom_index]/(nm_wavevectors*lop_nm_neighbors[atom_index])
            y = np.abs(x)**2
            accum_lop_terms_with_coeffs.accumulate(atom_index,y)
    return accum_lop_terms_with_coeffs

def calculate_sf_fcc_atom_order_parameter_no_coeffs(universe : MDA_Universe,
                                     wave_vectors: LatticeVectors,
                                     cutoff: float,
                                     accumulator_nm_neighbors: ArrayAccumulator,
                                     accumulator_lop_terms0: ArrayAccumulator)->tuple[np.ndarray,np.ndarray]:
    """ Calculates the FCC local order parameter exp(iq*r) for a set of atom
    coordinates.

    These terms do not factor in any coefficients.

    Args:
        universe: The MDAnalysis universe that contains all the atoms.

        wave_vectors: An numpy array of floats with array shape (N,3) where N
        is the number of wave vectors. The The [i,:] slice is the i'th
        wavevector.

        cutoff: The cutoff to search for neighboring atoms.

        accumulator_nm_neighbors: Caller-owned accumulator of neighbor counts
        per atom. The caller must reset it before each call.

        accumulator_lop_terms0: Caller-owned accumulator of exp(iq*r) terms
        per atom. The caller must reset it before each call.

    Returns:
        A tuple of a read-only view of the accumulated exp(iq*r) terms and a
        read-only view of the number of neighbors of each atom.
    """

    ar_atoms = universe.select_atoms("all")
    atom_coordinates = ar_atoms.positions
    box = universe.dimensions
    pairs = calculate_atom_pairs(atom_coordinates,cutoff,box)
    atom_pairs_vectors = calculate_atom_pairs_vectors(universe,pairs)

    # Create an accumulator over for each atom. For each atom we accumulate 
    # the number of neighbors and the exp(q*r) terms.
    (nm_wavevectors,_) = wave_vectors.shape

    accumulator_exp_x = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.complex64,
        capacity=np.int32(nm_wavevectors),
        initial_value=np.complex64(0.00),
        name="wavevector_exp_accumulator",
    )

    (nm_pairs,_) = pairs.shape
    for counter in range(nm_pairs):
        accumulator_exp_x.reset()
        atom_index1 = pairs[counter,0]
        atom_index2 = pairs[counter,1]
        dr = atom_pairs_vectors[counter]
        accumulator_nm_neighbors.accumulate(atom_index1, 1)
        accumulator_nm_neighbors.accumulate(atom_index2, 1)
        accum1 = calculate_lop_fcc_atom_pair_exp_terms(dr,
                    wave_vectors,
                    accumulator_exp_x)
        accumulator_lop_terms0.accumulate(atom_index1, accum1)
        accumulator_lop_terms0.accumulate(atom_index2, accum1)
    return (accumulator_lop_terms0.finalize(),accumulator_nm_neighbors.finalize())

def create_atom_pair_key(atom1: np.int32,
                         atom2: np.int32):
    if atom1 <= atom2:
        key = f"{atom1}-{atom2}"
    else:
        key = f"{atom2}-{atom1}"
    return key

class LopSfFcc:
    """ A callable class that calculates a fcc local order parameter. """

    md_params_schema_filepath = os.path.join(os.getenv("LTAT_TOP_LEVEL"),
        "src","lammps_trajectory_analysis_tools","schemas",
        "md_params.schema.json")

    def __init__(self)->None:
        self._wavevectors = None
        self._parallel_threads = 1

        # These attributes store the simulation parameters as a JSON
        # file and the corresponding JSON schema file for validation.
        self._md_params_json = None

        # These attributes store universe related data.
        self._universe = None
        self._nm_frames = None
        self._nm_atoms = None

        # These attributes are related to the neigbor search radius.
        self._neighbor_search_radius = None

        # The attributes store the accumulators needed to calculate the FCC LOP.
        self._accumulator_nm_neighbors = None
        self._accumulator_lop_terms0 = None
        self._accum_lop_terms_with_coeffs = None

        # These attributes are for writing results to hdf files.
        self._data_writer = None

    def _set_attributes(self,command_line_arguments:CLILopSfFcc)->None:
        """ Sets the attributes of this class. """

        # Set the number of parallel threads.
        self._parallel_threads = command_line_arguments.parallel_threads

        # Set the wavevectors.
        self._wavevectors = _set_attribute_wavevectors(command_line_arguments)

        # Set the json atributes
        self._md_params_json = (
            _set_md_params_attributes(command_line_arguments)
        )

        # Set the universe related attributes
        self._universe, self._nm_frames, self._nm_atoms = (
            _set_universe_attributes(command_line_arguments)
        )

        # Set the neighbor search radius.
        self._neighbor_search_radius = np.float32(command_line_arguments.cutoff)

        # Set the accumulators.
        (self._accum_lop_terms_with_coeffs, 
        self._accumulator_nm_neighbors, 
        self._accumulator_lop_terms0) = _set_accumulator_attributes(self._nm_atoms)

        # Set the data writer attributes.
        ( self._data_writer) = _set_data_writer_attributes(command_line_arguments,
                                                           self._md_params_json)



    def __call__(self, command_line_arguments:CLILopSfFcc) -> Any:

        self._set_attributes(command_line_arguments)

        # Loop over each trajectory and calculate the lop fcc fcc
        nm_wavevectors,_ = self._wavevectors.shape

        # Another accumulator reused and reset every frame.
        # accum_lop_terms_with_coeffs = array_accumulator_builder_registry.build(
        #     array_accumulator_builder_key,
        #     dtype=np.float64,
        #     capacity=np.int32(self._nm_atoms),
        #     initial_value=np.float64(0.00),
        #     name="atom_exp_terms_accumulator",
        # )

        print(f"Number of trajectory frames = {self._nm_frames}")
        report_iteration = 5
        max_trajectories_to_compute = 100
        trajectory_loop_timer = (
            timer_object_factory.build(LoopTimerBuilderKey,"trajectory_loop",max_trajectories_to_compute,report_iteration)
        )
        trajectory_loop_timer.start()
        counter = 0
        for ts in self._universe.trajectory:
            frame_index = ts.frame
            frame_time = ts.time

            self._accumulator_nm_neighbors.reset()
            self._accumulator_lop_terms0.reset()
            self._accum_lop_terms_with_coeffs.reset()

            (lop_terms0,nm_neighbors) = (
                calculate_sf_fcc_atom_order_parameter_no_coeffs(
                    self._universe,
                    self._wavevectors,
                    self._neighbor_search_radius,
                    self._accumulator_nm_neighbors,
                    self._accumulator_lop_terms0)
            )

            accum_lop_terms1 = (
                calculate_sf_fcc_atom_order_parameter_with_coeffs(
                    self._nm_atoms,
                    nm_wavevectors,
                    lop_terms0,
                    nm_neighbors,
                    self._accum_lop_terms_with_coeffs))

            counter += 1
            trajectory_loop_timer.update(counter)

            if counter == max_trajectories_to_compute:
                break
        trajectory_loop_timer.stop()
        return

# ----------
# Private members
# ----------

def _set_data_writer_attributes(command_line_arguments:CLILopSfFcc,
                                md_params_json)->None:
    hdf_file_name = command_line_arguments.output_hdf5_file
    md_params_json = command_line_arguments.md_params_json
    
    return None

def _set_attribute_wavevectors(
        command_line_arguments:CLILopSfFcc)->LatticeVectors:
    # We get the edge length of the fcc lattice and define
    # reciprocal lattice vectors for this edge length.
    edge_length = np.float64(command_line_arguments.edge_length)

    # Form the wavevectors from the fcc edge length.
    wavevectors = create_wavevectors(edge_length)
    return wavevectors

def _set_universe_attributes(command_line_arguments:CLILopSfFcc)->tuple[Any,...]:
    my_positional_args,my_keyword_args = create_mdanalysis_arguments(command_line_arguments)
    my_universe = load_universe(my_positional_args["topology_path"],
                                my_positional_args["trajectory_source"],
                                **my_keyword_args)

    # Loop over each trajectory and calculate the lop fcc fcc
    nm_frames = my_universe.trajectory.n_frames
    nm_atoms = my_universe.atoms.n_atoms
    return my_universe, nm_frames, nm_atoms 

def _set_accumulator_attributes(nm_atoms)->tuple[Any,...]:
    # One accumulator reused and reset every frame.
    accumulator_nm_neighbors = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.int32,
        capacity=np.int32(nm_atoms),
        initial_value=np.int32(0),
        name="atom_neighbor_accumulator",
    )

    # Another accumulator reused and reset every frame.
    accumulator_lop_terms0 = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.complex64,
        capacity=np.int32(nm_atoms),
        initial_value=np.complex64(0.00),
        name="atom_exp_terms_accumulator",
    )

    # Another accumulator reused and reset every frame.
    accum_lop_terms_with_coeffs = array_accumulator_builder_registry.build(
        array_accumulator_builder_key,
        dtype=np.float64,
        capacity=np.int32(nm_atoms),
        initial_value=np.float64(0.00),
        name="atom_exp_terms_accumulator",
    )

    return accum_lop_terms_with_coeffs, accumulator_nm_neighbors, accumulator_lop_terms0

def _set_md_params_attributes(
        command_line_arguments:CLILopSfFcc)->tuple[Any,...]:
    validate_json_file(command_line_arguments.md_params_json,
                       LopSfFcc.md_params_schema_filepath)
    md_params_json = read_json_file(command_line_arguments.md_params_json)
    return md_params_json



def _main()->None:
    pass

if __name__ == "__main__":
    _main()

