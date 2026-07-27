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
from lop_sf_fcc.lop_sf_fcc import create_reciprocal_lattice_vectors
from lop_sf_fcc.lop_sf_fcc import create_primitive_lattice_vectors
from data_types import AtomCoordinates,LatticeVectors
from data_types import AtomPairs
from data_types import TimeStep, TimeUnits
from data_types import Box
from data_types import AtomPairs

class Ar4Version0:
    def __init__(self):
        # We define the edge length in angstroms of the FCC lattice structure.
        self._edge_length: np.float64 = np.float64(5.19)

        """ The box dimensions of all trajectories.

        _box : An numpy 1d array floats of len 6. This is the box dimensions of
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
        self._edge_scaling_factor: np.float64 = np.float64(10.0)
        self._box: Box = _create_right_rectangular_box(self._edge_scaling_factor,
            self._edge_length)

        """ A atomic system of 4 atoms with an edge length equal to 1.00 angstroms"""
        self._coordinates1: AtomCoordinates = np.array([
            [0.00, 0.00, 0.00],
            [1.01, 0.00, 0.00],
            [0.50, 0.00, 0.50],
            [0.00, 0.00, 1.01]],dtype=np.float64)

        """ The atoms atomic coordinates. """
        self._coordinates: AtomCoordinates = (
            _scale_atom_coordinates(self._coordinates1,self._box))

        """ The reciprocal lattice vectors of the FCC structure. """
        self._reciprocal_lattice_vectors: LatticeVectors = (
            create_reciprocal_lattice_vectors(self._edge_length))

        """ The lattice vectors of the FCC structure. """
        self._primitive_lattice_vectors: LatticeVectors = (
            create_primitive_lattice_vectors(self._edge_length))

        """ The absolute path to the PSF file. """
        self._psf_filepath: str = (
            os.path.join(os.getenv("LTAT_TOP_LEVEL"),"tests","input_files","ar4.psf"))

        """ The units of the time step"""
        self._timeunits: TimeUnits = "ps"

        """ The magnitude of the time step. """
        self._dt: TimeStep = np.float64(1.0)

        # cls.cutoff = 1.0*cls.edge_length
        self._cutoff = 0.5*self._edge_length

        """ The correct atom pairs for cutoff and set of atoms. """
        self._atom_pairs: AtomPairs = (
            np.array([[0,1],[0,3],[1,3]],dtype=np.int32))

        """ The correct atom pairs vectors adjusted for pbc conditions.

        self._atom_pairs_vectors[0] = atom position 1 - atom position 0
        self._atom_pairs_vectors[1] = atom position 3 - atom position 0
        self._atom_pairs_vectors[2] = atom position 3 - atom position 1
        """
        self._atom_pairs_vectors: LatticeVectors = np.array(
            [[0.519, 0.00, 0.00],
             [0.00, 0.00, 0.519],
            [-0.519, 0.00, 0.519]], dtype=np.float64)

        """ The correct reciprocal lattice vectors of the unit FCC lattice.
    
        If this array is modified, one breaks this test.
        """
        self._correct_reciprocal_lattice_vectors: LatticeVectors = np.array(
            [[-0.6053165, 0.6053165, 0.6053165],
             [ 0.6053165, -0.6053165, 0.6053165],
             [ 0.6053165,  0.6053165, -0.6053165]],dtype=np.float64)

        """ The correct wave vectors of the unit FCC lattice. """
        self._wave_vectors = _create_wavevectors()

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
        return self._cutoff

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
    def lattice_edge_length(self)->np.float64:
        return self._edge_length

    @property
    def atom_pairs(self)->AtomPairs:
        return self._atom_pairs

    @property
    def atom_pairs_vectors(self)->LatticeVectors:
        return self._atom_pairs_vectors

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
            print(f"atom_coordinates{[row_index,col_index]}={atom_coordinates[row_index,col_index]}")
            print(f"scaled_coordinates{[row_index,col_index]}={scaled_coordinates[row_index,col_index]}")
            print()

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

def _create_wavevectors()->LatticeVectors:
    """ The wave vectors are a linear combination of the reciprocal lattice vectors.

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



def _main():
    return

if __name__ == "__main__":
    _main()
