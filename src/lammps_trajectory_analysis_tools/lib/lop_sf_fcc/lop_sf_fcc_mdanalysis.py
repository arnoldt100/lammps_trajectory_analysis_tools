#! /usr/bin/env python3
""" This module contains the MDAnalysis analysis class LOP_SF_FCC.

The public members provided by this module are:

    LOP_SF_FCC : An MDAnalysis analysis class.
"""

# Third party library imports
import numpy as np
from MDAnalysis.analysis.base import AnalysisBase
from MDAnalysis.analysis.results import Results, ResultsGroup

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
)
from lammps_trajectory_analysis_tools.lib.data_types import LatticeVectors

# ----------
# Public members
# ----------

class LOP_SF_FCC(AnalysisBase):
    r"""Calculates the FCC structure-factor local order parameter per atom
    over a range of trajectory frames.

    For atom :math:`j` with :math:`N_j` neighbors within ``cutoff`` and the
    six FCC wavevectors :math:`\mathbf{q}`, the order parameter is

    .. math::

        S_j = \left| \frac{1}{6 N_j} \sum_{k \in N_j} \sum_{\mathbf{q}}
              e^{i \mathbf{q} \cdot \mathbf{r}_{jk}} \right|^2

    Atoms with no neighbors have :math:`S_j = 0`.

    Parameters
    ----------
    atomgroup : MDAnalysis.core.groups.AtomGroup
        The atoms to analyse. Neighbors are searched within this group only.
    edge_length : float
        The FCC lattice edge length in angstroms.
    cutoff : float
        The neighbor-search cutoff in angstroms.
    data_writer : LopSfFccTrajectoryWriterValueObjectInterface, optional
        If given, ``_conclude`` writes every analysed frame to it. The target
        is created on the first ``run()`` and appended to on later runs.
        If ``None`` (default), results are only kept in memory.
    **kwargs
        Passed to :class:`MDAnalysis.analysis.base.AnalysisBase`
        (e.g. ``verbose``).

    Attributes
    ----------
    results.lop_sf_fcc : numpy.ndarray
        Array of shape ``(n_frames, n_atoms)`` with the order parameter of
        each atom in each analysed frame.
    results.box_lengths : numpy.ndarray
        Array of shape ``(n_frames, 3)`` with the box edge lengths.
    results.box_angles : numpy.ndarray
        Array of shape ``(n_frames, 3)`` with the box angles in degrees.
    results.positions : numpy.ndarray
        Array of shape ``(n_frames, n_atoms, 3)`` with the atom positions.
    frames : numpy.ndarray
        The analysed frame indices (set by ``AnalysisBase``).
    times : numpy.ndarray
        The analysed frame times (set by ``AnalysisBase``).

    Notes
    -----
    Periodic displacement vectors assume a right rectangular box.

    Supported backends are ``'serial'`` and ``'multiprocessing'``; pass
    ``backend`` and ``n_workers`` to :meth:`run`. Frames are calculated in
    the workers, but the data writer is used only by ``_conclude`` in the
    main process, after the worker results are merged in frame order.
    """

    _analysis_algorithm_is_parallelizable = True

    @classmethod
    def get_supported_backends(cls):
        return ('serial', 'multiprocessing')

    def __init__(self, atomgroup, edge_length, cutoff, data_writer=None, **kwargs):
        super().__init__(atomgroup.universe.trajectory, **kwargs)
        self._atomgroup = atomgroup
        self._nm_atoms = atomgroup.n_atoms
        self._cutoff = np.float32(cutoff)
        self._wavevectors = create_wavevectors(np.float64(edge_length))
        self._nm_wavevectors = self._wavevectors.shape[0]
        self._data_writer = data_writer
        self._data_writer_created = False
        self._nm_frames_written = 0

    def __getstate__(self):
        # Pickled copies (worker copies) never write; _prepare rebuilds the accumulators.
        state = self.__dict__.copy()
        state["_data_writer"] = None
        for name in ("_accumulator_nm_neighbors",
                     "_accumulator_lop_terms0",
                     "_accum_lop_terms_with_coeffs"):
            state.pop(name, None)
        return state

    def run(self, *args, **kwargs):
        # Otherwise results of an earlier run are pickled into every worker.
        self.results = Results()
        return super().run(*args, **kwargs)

    def _get_aggregator(self):
        return ResultsGroup(lookup={
            "lop_sf_fcc": ResultsGroup.ndarray_vstack,
            "box_lengths": ResultsGroup.ndarray_vstack,
            "box_angles": ResultsGroup.ndarray_vstack,
            "positions": ResultsGroup.ndarray_vstack,
        })

    def _prepare(self):
        self.results.lop_sf_fcc = np.zeros((self.n_frames, self._nm_atoms),
                                           dtype=np.float64)
        self.results.box_lengths = np.zeros((self.n_frames, 3), dtype=np.float64)
        self.results.box_angles = np.zeros((self.n_frames, 3), dtype=np.float64)
        self.results.positions = np.zeros((self.n_frames, self._nm_atoms, 3),
                                          dtype=np.float32)

        self._accumulator_nm_neighbors = array_accumulator_builder_registry.build(
            array_accumulator_builder_key,
            dtype=np.int32,
            capacity=np.int32(self._nm_atoms),
            initial_value=np.int32(0),
            name="atom_neighbor_accumulator",
        )
        self._accumulator_lop_terms0 = array_accumulator_builder_registry.build(
            array_accumulator_builder_key,
            dtype=np.complex64,
            capacity=np.int32(self._nm_atoms),
            initial_value=np.complex64(0.00),
            name="atom_exp_terms_accumulator",
        )
        self._accum_lop_terms_with_coeffs = array_accumulator_builder_registry.build(
            array_accumulator_builder_key,
            dtype=np.float64,
            capacity=np.int32(self._nm_atoms),
            initial_value=np.float64(0.00),
            name="atom_lop_terms_with_coeffs_accumulator",
        )

    def _single_frame(self):
        self._accumulator_nm_neighbors.reset()
        self._accumulator_lop_terms0.reset()
        self._accum_lop_terms_with_coeffs.reset()

        (lop_terms0, nm_neighbors) = (
            calculate_sf_fcc_atom_order_parameter_no_coeffs(
                self._atomgroup,
                self._wavevectors,
                self._cutoff,
                self._accumulator_nm_neighbors,
                self._accumulator_lop_terms0))

        lop_terms1 = calculate_sf_fcc_atom_order_parameter_with_coeffs(
            self._nm_atoms,
            self._nm_wavevectors,
            lop_terms0,
            nm_neighbors,
            self._accum_lop_terms_with_coeffs)

        # Row assignment copies; finalize() views are overwritten next frame.
        self.results.lop_sf_fcc[self._frame_index] = lop_terms1.finalize()
        self.results.box_lengths[self._frame_index] = self._ts.dimensions[:3]
        self.results.box_angles[self._frame_index] = self._ts.dimensions[3:]
        self.results.positions[self._frame_index] = self._atomgroup.positions

    def _conclude(self):
        if self._data_writer is None:
            return
        if self._data_writer_created:
            context = self._data_writer.open_for_append()
        else:
            context = self._data_writer
        with context as writer:
            self._data_writer_created = True
            for row, frame_index in enumerate(self.frames):
                # One HDF5 trajectory group per analysed frame, numbered across runs.
                writer.append_trajectory_frames(self._nm_frames_written + row,
                                                frame_index,
                                                self.results.positions[row],
                                                self.results.lop_sf_fcc[row],
                                                self.results.box_lengths[row],
                                                self.results.box_angles[row])
        self._nm_frames_written += self.n_frames

def create_primitive_lattice_vectors(fcc_edge_length : np.float64):
    """ Returns a numpy array of shape (3,3).

    Parameters:
        fcc_edge_length : The length in angstroms of the fcc lattice structure
        edge.

    Returns: An numpy array of shape (3,3) where each element is a real
    number. The [i,:] slice is the i'th primitive lattice vector.
    """
    a = fcc_edge_length*np.array([0,1,1], dtype=np.float64)
    b = fcc_edge_length*np.array([1,0,1], dtype=np.float64)
    c = fcc_edge_length*np.array([1,1,0], dtype=np.float64)
    primitive_lattice_vectors = np.array([a,b,c],dtype=np.float64)
    return primitive_lattice_vectors

def create_reciprocal_lattice_vectors(fcc_edge_length : np.float64):
    """ Returns a numpy array of shape (3,3).

    Parameters:
        fcc_edge_length : The length in angstroms of the fcc lattice structure
                          edge.

    Return:
        An numpy array of shape (3,3) where each element is a real
        number. The [i,:] slice is the i'th reciprocal lattice vector.
    """
    primitive_lattice_vectors = create_primitive_lattice_vectors(fcc_edge_length)
    a = primitive_lattice_vectors[0,:]
    b = primitive_lattice_vectors[1,:]
    c = primitive_lattice_vectors[2,:]

    primitive_lattice_volume = np.dot(a,np.cross(b,c))

    k_a = np.cross(b,c)
    k_b = np.cross(c,a)
    k_c = np.cross(a,b)
    reciprocal_lattice_vectors = (
            (2.0*np.pi/primitive_lattice_volume)*np.array([k_a,k_b,k_c],dtype=np.float64))
    return reciprocal_lattice_vectors

def create_wavevectors(fcc_edge_length : np.float64):
    """ Returns a numpy array of shape (N,3).

    Parameters:
        fcc_edge_length : The length in angstroms of the fcc lattice structure
        edge.

    Returns: An numpy array of shape (N,3) where each element is a real
    number. The [i,:] slice is the i'th wavevector.
    """
    reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(fcc_edge_length)

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
    """ Calculates the sum of the exp(iq*r) for each wave vector q.

    Args:
        dr : The displacement vector
        wavevectors: The wave_vectors to form the dot product with dr. A numpy
        array of shape (N,3) where wavevectors[i,:] is the i'th wave vector.
        accumulator_exp_x: Accumulates exp(iq*dr) per wave vector.

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

def calculate_sf_fcc_atom_order_parameter_with_coeffs(nm_atoms: np.int32,
        nm_wavevectors: np.int32,
        lop_terms_no_coeffs: np.ndarray[tuple[int],np.dtype[np.complex64]],
        lop_nm_neighbors: np.ndarray[tuple[int],np.dtype[np.int32]],
        accum_lop_terms_with_coeffs: ArrayAccumulator)->ArrayAccumulator:
    """ Calculates the FCC local order parameter for each atom from the
    accumulated exp(iq*r) terms, factoring in the coefficients.

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
        if lop_nm_neighbors[atom_index] > 0:
            x = lop_terms_no_coeffs[atom_index]/(nm_wavevectors*lop_nm_neighbors[atom_index])
            y = np.abs(x)**2
            accum_lop_terms_with_coeffs.accumulate(atom_index,y)
    return accum_lop_terms_with_coeffs

def calculate_sf_fcc_atom_order_parameter_no_coeffs(atomgroup,
                                     wave_vectors: LatticeVectors,
                                     cutoff: float,
                                     accumulator_nm_neighbors: ArrayAccumulator,
                                     accumulator_lop_terms0: ArrayAccumulator)->tuple[np.ndarray,np.ndarray]:
    """ Calculates the FCC local order parameter exp(iq*r) terms for the atoms
    of an AtomGroup at the current frame.

    These terms do not factor in any coefficients.

    Args:
        atomgroup: The MDAnalysis AtomGroup to analyse. Atom indices in the
        returned arrays are local to this group.

        wave_vectors: An numpy array of floats with array shape (N,3) where N
        is the number of wave vectors. The [i,:] slice is the i'th wavevector.

        cutoff: The cutoff to search for neighboring atoms.

        accumulator_nm_neighbors: Caller-owned accumulator of neighbor counts
        per atom. The caller must reset it before each call.

        accumulator_lop_terms0: Caller-owned accumulator of exp(iq*r) terms
        per atom. The caller must reset it before each call.

    Returns:
        A tuple of a read-only view of the accumulated exp(iq*r) terms and a
        read-only view of the number of neighbors of each atom.
    """
    atom_coordinates = atomgroup.positions
    box = atomgroup.dimensions
    pairs = calculate_atom_pairs(atom_coordinates,cutoff,box)
    atom_pairs_vectors = _calculate_atom_pairs_vectors(atom_coordinates,box,pairs)

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

# ----------
# Private members
# ----------

def _calculate_atom_pairs_vectors(atom_coordinates, box, pairs):
    """ Returns r_j - r_i for each pair (i, j), wrapped by the minimum-image
    convention for a right rectangular box. Shape (n_pairs, 3).
    """
    box_lengths = box[0:3]
    disp_vectors = atom_coordinates[pairs[:,1]] - atom_coordinates[pairs[:,0]]
    pbc_delta = box_lengths*np.round(disp_vectors/box_lengths)
    return disp_vectors - pbc_delta

