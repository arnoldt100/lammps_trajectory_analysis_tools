#! /usr/bin/env python3

# Python standard library imports
import unittest
import os

# Third party library imports
import numpy as np
import numpy.typing as npt
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter
from lop_sf_fcc.lop_sf_fcc import create_wavevectors
from lop_sf_fcc.lop_sf_fcc import create_reciprocal_lattice_vectors
from lop_sf_fcc.lop_sf_fcc import create_primitive_lattice_vectors
from data_types import LatticeVectors, AtomCoordinates


class TestLopSfFcc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Creates an MDAnalysis universe of 4 Ar atoms.

        Given an FCC lattice with edge length "edge_length", a FCC structure of
        4 atoms is created. The atoms are then placed in a cubic box where each
        side is length 10*edge_length. The PSF file is read from disk. The
        number of atoms must be 4 atoms to match the PSF file. The atomic coordinates,
        box dimensions, and PSF are then used to create a single frame MDAnalysis universe
        for testing purposes.
        """

        """ A FCC structure of 4 atoms with an edge length equal to 1.00 angstroms"""
        cls.fcc_coordinates : AtomCoordinates = np.array([
            [0.00,0.00,0.00],
            [0.50,0.50,0.00],
            [0.50,0.00,0.50],
            [0.00,0.50,0.50]])

        # We define the edge length of the FCC lattice structure.
        cls.edge_length = np.float64(5.19) # Edge length in angstroms.

        """ The atoms atomic coordinates. """
        cls.atomic_coordinates : AtomCoordinates = cls.edge_length*cls.fcc_coordinates

        """ The lattice vectors of the FCC structure. """
        cls.primitive_lattice_vectors : LatticeVectors = create_primitive_lattice_vectors(cls.edge_length)

        """ The reciprocal lattice vectors of the FCC structure. """
        cls.reciprocal_lattice_vectors = create_reciprocal_lattice_vectors(cls.edge_length)

        """ The wave vectors of the FCC lattice. """
        cls.wave_vectors = create_wavevectors(cls.edge_length)

        """ The box dimensions of all trajectories.

        Create box dimensions for a single frame Format: [lx, ly, lz, alpha,
        beta, gamma] We create a cubic box with edge length
        "cls.edge_length*10". If the box is too small, then the
        mda.lib.nsgrid.FastNS has issues finding neighboring pairs.
        """
        edge_scaling_factor = 10.0
        (lx,ly,lz) = (cls.edge_length*edge_scaling_factor,
                      cls.edge_length*edge_scaling_factor,
                      cls.edge_length*edge_scaling_factor)
        (alpha,beta,gamma) = (90.0,90.0,90.0)
        cls.box_dimensions = (np.array([lx,ly,lz,alpha,beta,gamma],dtype=np.float64))

        """ The absolute path to the protein """
        cls.psf_filepath: str = os.path.join(os.getenv("LTAT_TOP_LEVEL"),"tests","input_files","ar4.psf") 

        """ The units of the time step"""
        cls.timeunits: str = "ps"

        """ The magnitude of the time step. """
        cls.dt: float = 1.0

        """  The cutoff for the searching for neighboring atoms. The cutoff
             must be less that half the box length.
        """
        cls.cutoff = 2.0*cls.edge_length

        # Create a MD Analysis universe for a single frame.
        cls.universe = _create_universe_single_frame(cls.atomic_coordinates,
                                                     cls.box_dimensions,
                                                     cls.psf_filepath,
                                                     cls.timeunits,
                                                     cls.dt)

    def test_rlv_plv_orthogonal(self):
        """ This test verifies the orthogonality of the principal and reciprocal lattice vectors.

        Given principal lattice vectors a, b and c,
        reciprocal lattice vector k_a is formed by k_a = (1/(2*pi*vol))bxc
        where vol = (axb)*c. This means k_a*b and k_a*c must equal 0. Similarly for
        k_b and k_c.
        """

        # The number of decimal places to compare that the dot products are
        # zero.
        places = 15

        # Indices 0, 1, and 2 respectively correspond to axis x,y and z.
        # The reciprocal lattice vectors are as follows:
        #   k_a = (1/(2*pi*vol))bxc --> reciprocal lattice vector with index 0 is perpendicular
        #   to principal lattice vectors with indices 1 and 2.
        #   k_b = (1/(2*pi*vol))cxa --> reciprocal lattice vector with index 1 is perpendicular
        #   to principal lattice vectors with indices 2 and 0.
        #   k_c = (1/(2*pi*vol))axb --> reciprocal lattice vector with index 2 is perpendicular
        #   to principal lattice vectors with indices 0 and 1.
        (rlv_a_index,rlv_b_index,rlv_c_index) = (0,1,2)
        (plv_a_index,plv_b_index,plv_c_index) = (0,1,2)
        indices_to_verify = np.array([[rlv_a_index,plv_b_index],
                            [rlv_a_index,plv_c_index],
                            [rlv_b_index,plv_c_index],
                            [rlv_b_index,plv_a_index],
                            [rlv_c_index,plv_a_index],
                            [rlv_c_index,plv_b_index]])

        # We loop over the reciprocal and primitive lattice vector indices
        # and verify the corresponding reciprocal and lattice vector dot
        # product is zero.
        for [rlv_index,plv_index] in indices_to_verify:
            message = _message_rlvplv_nonorthogonal(rlv_index,self.reciprocal_lattice_vectors[rlv_index,:],
                                                   plv_index,self.primitive_lattice_vectors[plv_index,:])
            dp = np.dot(self.reciprocal_lattice_vectors[rlv_index,:],
                        self.primitive_lattice_vectors[plv_index,:])
            self.assertAlmostEqual(dp,0.00,places,message)


    def test_fcc_ar4(self):
        # The number of decimal places to compare the local FCC order parameter.
        places = 15
        message = _message_a4_lop_sf()
        value = 0.01
        cutoff = self.cutoff

        ar_atoms = self.universe.select_atoms("all")
        box_dimensions =  self.universe.dimensions
        for ts in self.universe.trajectory:
            ar_atom_positions = ar_atoms.positions 
            # print(f"box dimensions=\n{ar_atoms.dimensions}")
            # print(f"ar_atom_positions=\n{ar_atom_positions}")
            calculate_sf_fcc_order_parameter(ar_atom_positions,
                                             self.wave_vectors,cutoff,
                                             box_dimensions)

        self.assertAlmostEqual(value,0.00,places,message)

    @classmethod
    def tearDownClass(cls):
        pass
#
# ----------
# Private members
# ----------

def _message_rlvplv_nonorthogonal(rlv_index: int, rlv: LatticeVectors,
                                 plv_index: int, plv: LatticeVectors)->str:
    """ Returns a string warning message that RLV and PLV vectors aren't orthogonal.

    rlv_index : The array index of the reciprocal lattice vector.

    rlv : A reciprocal lattice vector.

    plv_index : The array index of the principal lattice vector.

    plv : A principal lattice vector.

    """
    # The 1 index primitive lattice vector should be orthogonal to
    # the 2 and 0 index reciprocal lattice vectors.
    plv_index = 1
    rlv_index = 2
    message = f"The {rlv_index} index reciprocal lattice vector isn't orthogonal/n"
    message += f"to the {plv_index} index primitive lattice vector./n"
    message += f"reciprocal_lattice_vector[{rlv_index}]={rlv}/n"
    message += f"primitive_lattice_vector[{plv_index}]={plv}/n"
    return message

def _message_a4_lop_sf():
    message = "The local order parameter fcc structure factor is wrong."
    return message

def _create_universe_single_frame(atom_coordinates: AtomCoordinates, box_dimensions, psf_filepath: str,
                     timeunits: str, dt: float):
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
    (nm_atoms,_) =  atom_coordinates.shape
    box_array = np.array([box_dimensions for _ in range(nm_frames)])
    trajectory = np.array([atom_coordinates for _ in range(nm_frames)])
    universe  = mda.Universe(psf_filepath,trajectory,format=MemoryReader,dt=dt,
       dimensions=box_array)

    return universe

if __name__ == "__main__":
    unittest.main()
