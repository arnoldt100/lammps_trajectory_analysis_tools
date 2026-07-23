#! /usr/bin/env python3
""" Contains the protocol class for Ar structures for testing.

"""

# Python standard library imports
from typing import Protocol

# Third party library imports
import numpy as np

# Local Library package imports
from data_types import MDA_Universe
from data_types import AtomCoordinates, LatticeVectors
from data_types import TimeStep,TimeUnits
from data_types import Box

class ArLOPFCCTestStructure(Protocol):

    def create_md_analysis_universe(self)->MDA_Universe:
        raise NotImplementedError

    @property
    def coordinates(self)->AtomCoordinates:
        raise NotImplementedError

    @property
    def timeunits(self)->TimeUnits:
        raise NotImplementedError

    @property
    def timestep(self)->TimeStep:
        raise NotImplementedError

    @property
    def box(self)->Box:
        raise NotImplementedError

    @property
    def psf_filepath(self)->str:
        raise NotImplementedError

    @property
    def cutoff(self)->np.float64:
        raise NotImplementedError

    @property
    def reciprocal_lattice_vectors(self)->LatticeVectors:
        raise NotImplementedError

    @property
    def primitive_lattice_vectors(self)->LatticeVectors:
        raise NotImplementedError
