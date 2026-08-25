#! /usr/bin/env python3
""" This module contains the LopSfFccFactory definition.

The public members provided by this module are:

    key_lop_sf_fcc_factory
    LopSfFccFactory
"""

# Local imports
from  lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc import LopSfFcc

# ----------
# Public members
# ----------

""" The builder key that is uniquely associated with the class LopSfFccFactory

This key is used by other classes, especially the builder classes, to register the
class LopSfFccFactory. These concrete factory classes must be unique
or undefined behavior may occur.
"""
key_lop_sf_fcc_factory = "LopSfFccFactory"

class LopSfFccFactory:
    def __init__(self)->None:
        return

    def __call__(self,*kargs,**kwargs)->LopSfFcc:
        return LopSfFcc(*kargs,**kwargs)

# ----------
# Private members
# ----------

def _main()->None:
    pass


if __name__ == "__main__":
    _main ()

