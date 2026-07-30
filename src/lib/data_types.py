#! /usr/bin/env python3
"""Contains the fundamental types for typing """

from typing import Literal, TypeVar
import numpy as np

import MDAnalysis as mda

# The type for an MDAnalysis Universe.
type MDA_Universe = mda.core.universe.Universe

# A C-contiguous N x 3 array of float types for atomic positions
type AtomCoordinates16 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float16]]
type AtomCoordinates32 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float32]]
type AtomCoordinates64 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float64]]
AtomCoordinates = TypeVar('AtomCoordinates',
                          AtomCoordinates16,
                          AtomCoordinates32,
                          AtomCoordinates64)

# A C-contiguous N x 3 array of float types for reciprocal lattice vectors.
type LatticeVectors16 = np.ndarray[tuple[int,Literal[3]],np.dtype[np.float16]]
type LatticeVectors32 = np.ndarray[tuple[int,Literal[3]],np.dtype[np.float32]]
type LatticeVectors64 = np.ndarray[tuple[int,Literal[3]],np.dtype[np.float64]]
LatticeVectors = TypeVar('LatticeVectors',
                          LatticeVectors16,
                          LatticeVectors32,
                          LatticeVectors64)

# An integer array of Nx2 atom pairs
type AtomPairs16 = np.ndarray[tuple[int,Literal[2]],np.dtype[np.int16]]
type AtomPairs32 = np.ndarray[tuple[int,Literal[2]],np.dtype[np.int32]]
type AtomPairs64 = np.ndarray[tuple[int,Literal[2]],np.dtype[np.int64]]
AtomPairs = TypeVar("AtomPairs",
                    AtomPairs16,
                    AtomPairs32,
                    AtomPairs64)

# The type for the displacement vectors between a set of atom pairs.
type AtomDisplacement16 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float16]]
type AtomDisplacement32 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float32]]
type AtomDisplacement64 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float64]]
AtomDisplacement = TypeVar('AtomDisplacement',
                          AtomDisplacement16,
                          AtomDisplacement32,
                          AtomDisplacement64)

# The type for the box dimensions.
type Box16 =  np.ndarray[tuple[Literal[6]],np.dtype[np.float16]]
type Box32 =  np.ndarray[tuple[Literal[6]],np.dtype[np.float32]]
type Box64 =  np.ndarray[tuple[Literal[6]],np.dtype[np.float64]]
Box = TypeVar("Box",
               Box16,
               Box32,
               Box64)

# The type for the atom_pair_terms
type AtomPairsTerms = dict[str,np.ndarray[tuple[int],np.dtype[np.complex64]]]

# The type for the atom_pair_terms
type AtomExpAccumTerm = np.ndarray[tuple[int],np.dtype[np.complex64]]

# The type for the magnitude of time step.
type TimeStep16 = np.float16
type TimeStep32 = np.float32
type TimeStep64 = np.float64
TimeStep = TypeVar("TimeStep",
                   TimeStep16,
                   TimeStep32,
                   TimeStep64)

# The type for the units of time step.
type TimeUnits = str
