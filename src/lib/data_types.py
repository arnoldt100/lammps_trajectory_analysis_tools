#! /usr/bin/env python3
from typing import Literal, TypeVar
import numpy as np

# A C-contiguous N x 3 array of 32-bit floats for atomic positions
type AtomCoordinates16 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float16]]
type AtomCoordinates32 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float32]]
type AtomCoordinates64 = np.ndarray[tuple[int, Literal[3]], np.dtype[np.float64]]
AtomCoordinates = TypeVar('AtomCoordinates', AtomCoordinates16, AtomCoordinates32, AtomCoordinates64)

