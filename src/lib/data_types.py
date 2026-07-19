#! /usr/bin/env python3
"""Contains the fundamental types for typing """

from typing import Literal, TypeVar
import numpy as np

# A C-contiguous N x 3 array of float types for atomic positions
type AtomCoordinates16 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float16]]
type AtomCoordinates32 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float32]]
type AtomCoordinates64 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float64]]
AtomCoordinates = TypeVar('AtomCoordinates', AtomCoordinates16, AtomCoordinates32, AtomCoordinates64)

# A C-contiguous N x 3 array of float types for reciprocal lattice vectors.
type LatticeVectors16 = np.ndarray[tuple[int,Literal[3]],np.dtype[np.float16]]
type LatticeVectors32 = np.ndarray[tuple[int,Literal[3]],np.dtype[np.float32]]
type LatticeVectors64 = np.ndarray[tuple[int,Literal[3]],np.dtype[np.float64]]
LatticeVectors = TypeVar('LatticeVectors',
                          LatticeVectors16,
                          LatticeVectors32,
                          LatticeVectors64)
