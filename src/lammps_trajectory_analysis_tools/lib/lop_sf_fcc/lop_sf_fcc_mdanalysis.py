
import os
import numpy as np

from MDAnalysis.analysis.base import AnalysisBase

class LOP_SF_FCC(AnalysisBase):
    r"""Calculates the Face Centered Cubic local order parameter accross a trajectory.

    For now this analysis class creates an integer array with length of the
    trajectory. Let the trajectory have length N. Running this analysis tool
    creats an integer array that contains values from 0 to N-1. The calculation
    on frame N puts integer value N-1 in location N-1.
    """

    @classmethod
    def get_supported_backends(cls):
        return ('serial', )

    def __init__(self,atom_group,**kwargs):
        super().__init__(atom_group.universe.trajectory,**kwargs)
        self._atom_group = atom_group
        self._nm_frames = 0
        self._nm_atoms = 0
        self.results.lop_sf_fcc = []

    def _prepare(self):
        self._nm_frames = self._atom_group.universe.trajectory.n_frames
        self._nm_atoms = self._atom_group.n_atoms
        self.results.lop_sf_fcc = []

    def _single_frame(self):
        # REQUIRED
        # Called after the trajectory is moved onto each new frame.
        # store an example_result of `some_function` for a single frame
        self.results.lop_sf_fcc.append(dummy_function(self._atom_group))

    def _conclude(self):
        print(self.results.lop_sf_fcc)

def dummy_function(*args,**kwargs)->int:
    return 1

