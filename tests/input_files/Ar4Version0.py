#! /usr/bin/env python3
""" Contains the data class for the Ar4 version 0 structure.

This structure has 4 argon atoms at fcc lattice coordinates.
"""

# Python standard library imports
import os
import re

# Third party library imports
import numpy as np
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import (create_reciprocal_lattice_vectors,
 create_primitive_lattice_vectors)

from accumulator.array_accumulator import ArrayAccumulator

from data_types import ( AtomCoordinates,LatticeVectors,
    AtomPairs, AtomPairsTerms, TimeStep,
    TimeUnits, Box)

class Ar4Version0:
    def __init__(self):
        """ The absolute path to the PSF file. 

        Do not modify. Modification will break this test configuration.
        """
        self._psf_filepath: str = (
            os.path.join(os.getenv("LTAT_TOP_LEVEL"),"tests","input_files","ar4.psf"))

        """ We define the edge length in angstroms of the FCC lattice structure.

        Do not modify. Modification will berak this test configuration.
        """
        self._edge_length: np.float64 = np.float64(5.19)

        """ The scaling factor setting the containing box and the atomic coordinates.

        Do not modify. Modification will break this test configuration.
        """
        self._edge_scaling_factor: np.float64 = np.float64(10.0)

        """ The box dimensions of all trajectories.

        _box : An numpy 1d array floats of length 6. This is the box dimensions of
        the atomic coordinates in "atom_coordinates" where:
            box_dimensions[0] = x-axis length in angstroms
            box_dimensions[1] = y-axis length in angstroms
            box_dimensions[2] = z-axis length in angstroms
            box_dimensions[3] = Angle between y and z axis in degrees
            box_dimensions[4] = Angle between x and z axis in degrees
            box_dimensions[5] = Angle between x and y axis in degrees

        Create box dimensions for a single frame Format: [lx, ly, lz, alpha,
        beta, gamma] We create a cubic box with edge length
        "cls.edge_length*10". If the box is too small, then the
        neighbor search algorithm has issues finding neighboring pairs.
        """
        self._box: Box = _create_right_rectangular_box(self._edge_scaling_factor,
            self._edge_length)
        
        """ A atomic system of 4 atoms with an edge length equal to 1.00 angstroms

        Do not modify. Modification will berak this test configuration.
        """
        self._coordinates1: AtomCoordinates = np.array([
            [0.00, 0.00, 0.00],
            [1.01, 0.00, 0.00],
            [0.50, 0.00, 0.50],
            [0.00, 0.00, 1.01]],dtype=np.float64)


        """ The atoms atomic coordinates. """
        self._coordinates: AtomCoordinates = (
            _scale_atom_coordinates(self._coordinates1,self._box))

        """ The number of atoms in the system. """
        self._nm_atoms: np.int32 =_compute_nm_atoms(self._coordinates)

        """ The reciprocal lattice vectors of the FCC structure. """
        self._reciprocal_lattice_vectors: LatticeVectors = (
            create_reciprocal_lattice_vectors(self._edge_length))

        """ The lattice vectors of the FCC structure. """
        self._primitive_lattice_vectors: LatticeVectors = (
            create_primitive_lattice_vectors(self._edge_length))

        """ The units of the time step"""
        self._timeunits: TimeUnits = "ps"

        """ The magnitude of the time step. """
        self._dt: TimeStep = np.float64(1.0)

        # cls.cutoff = 1.0*cls.edge_length
        self._cutoff = 0.5*self._edge_length

        """ The correct atom pairs for cutoff and set of atoms. 

        Do not modify. Modification will break this test configuration.
        """
        self._atom_pairs: AtomPairs = (
            np.array([[0,1],[0,3],[1,3]],dtype=np.int32))

        """ The number of neighbors for each atom. 

        Do not modify. Modification will break this test configuration.
        """
        self.accum_lop_nm_neighbors= np.array([2,2,0,2],dtype=np.int32)

        """ The correct atom pairs vectors adjusted for pbc conditions.

        self._atom_pairs_vectors[0] = atom position 1 - atom position 0
        self._atom_pairs_vectors[1] = atom position 3 - atom position 0
        self._atom_pairs_vectors[2] = atom position 3 - atom position 1

        Do not modify. Modification will break this test configuration.
        """
        self._atom_pairs_vectors: LatticeVectors = np.array(
            [[0.519, 0.00, 0.00],
             [0.00, 0.00, 0.519],
            [-0.519, 0.00, 0.519]], dtype=np.float64)

        """ The correct reciprocal lattice vectors of the unit FCC lattice.

        Do not modify. Modification will break this test configuration.
        """
        self._correct_reciprocal_lattice_vectors: LatticeVectors = np.array(
            [[-0.6053165, 0.6053165, 0.6053165],
             [ 0.6053165, -0.6053165, 0.6053165],
             [ 0.6053165,  0.6053165, -0.6053165]],dtype=np.float64)

        """ The correct wave vectors of the unit FCC lattice. """
        self._wave_vectors = _create_reference_wavevectors()

        """ The number of wave_vectors. """
        self._nm_wavevectors: np.int32 = _compute_nm_wavevectors(self._wave_vectors)

        """ The exp(iq*r) terms for the atom pair terms.

        The exp(iq*r) for each wavevector q.
        """
        self._atom_pairs_exp_terms: AtomPairsTerms = (
            _create_atom_pairs_exp_terms())

        """ The accumulated exp(iq*r) terms for each atom."""
        (nm_atoms,_) = self._coordinates.shape
        self._accum_atom_exp_terms_no_coeffs: ArrayAccumulator = (
            _create_accum_atom_exp_terms_no_coeffs(self._atom_pairs_exp_terms,
                                         np.int32(nm_atoms)))

        self._accum_atom_exp_terms_with_coeffs: np.ndarray = (
            _create_accum_atom_exp_terms_with_coeffs(
                self._atom_pairs_exp_terms,
                np.int32(nm_atoms),
                self._wave_vectors))


    def create_md_analysis_universe(self):
        """ Creates a MDAnalysis universe for a single trajectory from a single set of atomic coordinates.

        atom_coordinates : An numpy array of floats of shape (nm_atoms,3).

        box_dimensions : An numpy 1d array floats of len 6. This is the box dimensions of
        the atomic coordinates in "atom_coordinates" where:
            box_dimensions[0] = x-axis length in angstroms
            box_dimensions[1] = y-axis length in angstroms
            box_dimensions[2] = z-axis length in angstroms
            box_dimensions[3] = Angle between y and z axis in degrees
            box_dimensions[4] = Angle between x and z axis in degrees
            box_dimensions[5] = Angle between x and y axis in degrees

        psf_filepath : A string of the file path to the psf of "atom_coordinates". 

        timesunits : A string of the time units.

        dt : The magnitude of the time step.

        """
        nm_frames = 1
        box_array = np.array([self.box for _ in range(nm_frames)])
        trajectory = np.array([self.coordinates for _ in range(nm_frames)])
        universe = mda.Universe(self.psf_filepath,
                                trajectory,
                                format=MemoryReader,
                                dt=self.timestep,
                                dimensions=box_array)
        return universe

    @property
    def structure_identification(self):
        return "Ar4Version0"

    @property
    def coordinates(self)->AtomCoordinates:
        return self._coordinates

    @property
    def nm_atoms(self):
        return self._nm_atoms

    @property
    def timeunits(self)->TimeUnits:
        return self._timeunits

    @property
    def timestep(self)->TimeStep:
        return self._dt

    @property
    def box(self):
        return self._box

    @property
    def psf_filepath(self)->str:
        return self._psf_filepath

    @property
    def cutoff(self)->np.float64:
        return np.float64(self._cutoff)

    @property
    def reciprocal_lattice_vectors(self)->LatticeVectors:
        return self._reciprocal_lattice_vectors

    @property
    def primitive_lattice_vectors(self)->LatticeVectors:
        return self._primitive_lattice_vectors

    @property
    def wave_vectors(self)->LatticeVectors:
        return self._wave_vectors

    @property
    def nm_wavevectors(self)->np.int32:
        return self._nm_wavevectors

    @property
    def lattice_edge_length(self)->np.float64:
        return self._edge_length

    @property
    def atom_pairs(self)->AtomPairs:
        return self._atom_pairs

    @property
    def atom_pairs_vectors(self)->LatticeVectors:
        return self._atom_pairs_vectors

    @property
    def atom_pairs_exp_terms(self)->AtomPairsTerms:
        return self._atom_pairs_exp_terms

    @property
    def atom_accum_exp_terms_nocoeffs(self)->ArrayAccumulator:
        return self._accum_atom_exp_terms_no_coeffs

    @property
    def atom_accum_exp_terms_with_coeffs(self)->ArrayAccumulator:
        return self._accum_atom_exp_terms_with_coeffs

def _compute_nm_atoms(coordinates: AtomCoordinates)->np.int32:
    (nm_atoms,_) = coordinates.shape
    return np.int32(nm_atoms)

def _compute_nm_wavevectors(wavevectors: LatticeVectors)->np.int32:
    (nm_wavevectors,_) = wavevectors.shape
    return np.int32(nm_wavevectors)

def _scale_atom_coordinates(atom_coordinates: AtomCoordinates, box: Box):
    """ Scales the atoms coordinates by the length of ege in box.

    Each coordinate in "atom_coordinates" is scaled by "box[0,3]"

    Parameters:
        atom_coordinates :  An numpy array of floats of shape (nm_atoms,3).

        box : The box that will contain the scaled coordinates. 
              An numpy 1d array floats of len 6. This is the box dimensions of
              the atomic coordinates in "atom_coordinates" where:
              box_dimensions[0] = x-axis length in angstroms 
              box_dimensions[1] = y-axis length in angstroms
              box_dimensions[2] = z-axis length in angstroms
              box_dimensions[3] = Angle between y and z axis in degrees
              box_dimensions[4] = Angle between x and z axis in degrees
              box_dimensions[5] = Angle between x and y axis in degrees
    """
    (nm_rows,nm_cols) = atom_coordinates.shape
    scaled_coordinates = np.zeros((nm_rows,nm_cols),np.float64)
    for row_index in range(nm_rows):
        for col_index in range(nm_cols):
            scaled_coordinates[row_index,col_index] = (
                atom_coordinates[row_index,col_index]*box[col_index] )

    return scaled_coordinates

def _create_right_rectangular_box(edge_scaling_factor: np.float64,
                                  edge_length: np.float64)->Box:
    """ Creates a MDAnalysis containing box for the atomic system.

    The containing box is a right rectangular box.

    Args:
        edge_scaling_factor: The multiplicative factor to scale the containing box
            edge.

        edge_length: The unscaled box edge length.

    """
    lattice_angles: np.float64 = np.float64(90.00)
    box_edge_length: np.float64 = edge_length*edge_scaling_factor
    box: Box = np.array([box_edge_length, box_edge_length, box_edge_length,
                         lattice_angles, lattice_angles, lattice_angles],
                         np.float64)
    return box

def _create_reference_wavevectors()->LatticeVectors:
    """ The reference wave vectors are a linear combination of the reciprocal lattice vectors.

    wv_0 = reciprocal_lattice_vectors[1] + reciprocal_lattice_vectors[2]
    wv_1 = reciprocal_lattice_vectors[0] + reciprocal_lattice_vectors[2]
    wv_2 = reciprocal_lattice_vectors[0] + reciprocal_lattice_vectors[1]
    wv_3 = wv_0 + wv_1
    wv_4 = wv_0 - wv_1
    wv_5 = wv_1 + wv_2

    If this function returns a different array, one breaks this test.
    """
    wavevectors = np.array([[ 1.210633, 0.00, 0.0 ],
                            [ 0.00, 1.210633, 0.00],
                            [ 0.00, 0.00, 1.210633],
                            [ 1.210633, 1.210633, 0.00],
                            [ 1.210633, -1.210633,  0.00],
                            [ 0.00, 1.210633, 1.210633]],dtype=np.float64)
    return wavevectors


def _create_atom_pairs_exp_terms()->AtomPairsTerms:
    """ If this array is modified, one breaks this test. """
    atom_pairs_terms = {}
    atom_pairs_terms["0-1"] = np.array([0.8090189944341818+0.5877824994372538j,
                                        1.00 + 0j,
                                        1.00 + 0j,
                                        0.8090189944341818+0.5877824994372538j,
                                        0.8090189944341818+0.5877824994372538j,
                                        1.00 + 0j],dtype=np.complex64)

    atom_pairs_terms["0-3"] = np.array([1.00 + 0j,
                                        1.00 + 0j,
                                        0.8090189944341818+0.5877824994372538j,
                                        1.00 + 0j,
                                        1.00 + 0j,
                                        0.8090189944341818+0.5877824994372538j],dtype=np.complex64)

    atom_pairs_terms["1-3"] = np.array([0.8090189944341818-0.5877824994372538j,
                                        1.00 + 0j,
                                        0.8090189944341818+0.5877824994372538j,
                                        0.8090189944341818-0.5877824994372538j,
                                        0.8090189944341818-0.5877824994372538j,
                                        0.8090189944341818+0.5877824994372538j],dtype=np.complex64)
    return atom_pairs_terms

def _create_accum_atom_exp_terms_no_coeffs(atom_pairs_exp_terms: AtomPairsTerms,
                                 nm_atoms: np.int32)->ArrayAccumulator:

    accum_exp_terms: ArrayAccumulator= ( ArrayAccumulator(np.complex64,
                                                          initial_value=0j,
                                                          capacity=4,
                                                          name="Reference Accumulated Atom exp Terms"))

    for key,value in atom_pairs_exp_terms.items():
        sum1 = np.sum(value)
        (atom_index1,atom_index2) = key.split('-')
        accum_exp_terms.accumulate(np.int32(atom_index1),sum1)
        accum_exp_terms.accumulate(np.int32(atom_index2),sum1)

    return accum_exp_terms

def _create_accum_atom_exp_terms_with_coeffs(atom_pairs_exp_terms: AtomPairsTerms,
                                             nm_atoms: np.int32,
                                             wavevectors: np.ndarray)->np.ndarray:

    print("\nIn method _create_accum_atom_exp_terms_with_coeffs")
    accum_exp_terms: ArrayAccumulator= ( ArrayAccumulator(np.complex64,
                                                          initial_value=0j,
                                                          capacity=4,
                                                          name="Reference Accumulated Atom exp Terms"))

    accum_lop_terms = np.zeros(nm_atoms,dtype=np.complex64)
    accum_lop_nm_neighbors = np.zeros(nm_atoms,dtype=np.int64)
    (nm_wavevectors,_) = wavevectors.shape
    for key,value in atom_pairs_exp_terms.items():
        sum1 = np.sum(value)
        (atom_index1,atom_index2) = key.split('-')
        accum_lop_terms[np.int32(atom_index1)]  += sum1
        accum_lop_terms[np.int32(atom_index2)]  += sum1
        accum_lop_nm_neighbors[np.int32(atom_index1)] += 1
        accum_lop_nm_neighbors[np.int32(atom_index2)] += 1

    print(f"accum_lop_terms_no_coeffs={accum_lop_terms}")

    accum_lop = np.zeros(nm_atoms,dtype=np.complex64)
    for atom_index in range(nm_atoms):
        print(f"Pre -accum_lop_terms_with_coeffs[{atom_index}] = {accum_lop[atom_index]}")
        x = np.complex64(0.00)
        if accum_lop_nm_neighbors[atom_index] > 0:
            x = accum_lop_terms[atom_index]
            y = np.abs(x)**2
            print(f"nm_wavevectors={nm_wavevectors}")
            print(f"accum_lop_nm_neighbors={accum_lop_nm_neighbors[atom_index]}")
            print(f"\ty={y}")
            accum_lop[atom_index] = y/((nm_wavevectors*accum_lop_nm_neighbors[atom_index])**2)
        print(f"Post accum_lop_terms_with_coeffs[{atom_index}] = {accum_lop[atom_index]}\n")
    print("Leaving method _create_accum_atom_exp_terms_with_coeffs\n")

    return accum_lop

def _main():
    return

if __name__ == "__main__":
    _main()
