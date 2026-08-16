"""
Trajectory I/O and data structures for LAMMPS simulations.

Provides classes and functions for reading, parsing, and storing LAMMPS trajectory files
in various formats (dump, lammpstrj, etc.).
"""

from typing import List, Union, Optional
from pathlib import Path
import numpy as np


class Frame:
    """
    A single timestep from a LAMMPS trajectory.
    
    Attributes:
        timestep: Simulation timestep number
        atoms: Atom positions and properties (N x D array)
        box: Simulation box dimensions and angles
        metadata: Additional frame-level metadata (temperature, pressure, etc.)
    """
    
    def __init__(
        self,
        timestep: int,
        atoms: np.ndarray,
        box: np.ndarray,
        metadata: Optional[dict] = None,
    ):
        """Initialize a Frame."""
        self._timestep = timestep
        self._atoms = atoms
        self._box = box
        self._metadata = metadata or {}

    @property
    def timestep(self) -> int:
        """Return the simulation timestep."""
        return self._timestep

    @property
    def atoms(self) -> np.ndarray:
        """Return the atom data for this frame."""
        return self._atoms

    @property
    def box(self) -> np.ndarray:
        """Return the simulation box data."""
        return self._box

    @property
    def metadata(self) -> dict:
        """Return the frame metadata."""
        return self._metadata
    
    def __repr__(self) -> str:
        return f"Frame(timestep={self.timestep}, n_atoms={len(self.atoms)})"


class TrajectoryReader:
    """
    Base reader for LAMMPS trajectory files.
    
    Detects file format and provides iterator interface over frames.
    """
    
    def __init__(self, filepath: Union[str, Path]):
        """Initialize reader with trajectory file path."""
        self._filepath = Path(filepath)
        if not self._filepath.exists():
            raise FileNotFoundError(f"Trajectory file not found: {self._filepath}")

    @property
    def filepath(self) -> Path:
        """Return the source trajectory path."""
        return self._filepath
    
    def __iter__(self):
        """Iterate over frames in trajectory."""
        raise NotImplementedError("Subclasses must implement __iter__")
    
    def read_all(self) -> List[Frame]:
        """Read all frames into memory."""
        return list(self)


class Trajectory:
    """
    In-memory container for trajectory frames.
    
    Provides convenient access to trajectory data with caching and slicing.
    """
    
    def __init__(self, frames: List[Frame]):
        """Initialize with list of Frame objects."""
        self._frames = frames

    @property
    def frames(self) -> List[Frame]:
        """Return the trajectory frames."""
        return self._frames
    
    def __len__(self) -> int:
        return len(self.frames)
    
    def __getitem__(self, idx: int) -> Frame:
        return self.frames[idx]
    
    @property
    def n_atoms(self) -> int:
        """Number of atoms (assumes constant across trajectory)."""
        if not self.frames:
            return 0
        return len(self.frames[0].atoms)
    
    @property
    def timesteps(self) -> np.ndarray:
        """Array of timestep numbers."""
        return np.array([frame.timestep for frame in self.frames])


def format_detector(filepath: Union[str, Path]) -> str:
    """
    Detect LAMMPS trajectory file format.
    
    Args:
        filepath: Path to trajectory file
        
    Returns:
        Format identifier ('lammpstrj', 'dump', etc.)
        
    Raises:
        ValueError: If format cannot be detected
    """
    raise NotImplementedError()


def read_dump(
    filepath: Union[str, Path],
    read_all: bool = True,
    **kwargs,
) -> Union[TrajectoryReader, Trajectory]:
    """
    Read LAMMPS trajectory file.
    
    Args:
        filepath: Path to trajectory file
        read_all: If True, load all frames into memory; else return iterator
        **kwargs: Format-specific options
        
    Returns:
        Trajectory object if read_all=True, else TrajectoryReader
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file format is unsupported
    """
    raise NotImplementedError()
