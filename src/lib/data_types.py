from typing import Literal, TypeAlias
import numpy as np

# A C-contiguous N x 3 array of 32-bit floats for atomic positions
AtomCoordinates: TypeAlias = np.ndarray[tuple[int, Literal], np.dtype[np.float32]]

