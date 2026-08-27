#! /usr/bin/env python3
""" This module contains the LopSfFccBuilder definition.

The public members provided by this module are:

    lop_sf_fcc_builder_key
    LopSfFccBuilder
"""

# Local imports
from  lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc import LopSfFcc

# ----------
# Public members
# ----------

""" The builder key that is uniquely associated with the class LopSfFccBuilder

This key is used by other classes, especially the builder classes, to register the
class LopSfFccBuilder. These concrete factory classes must be unique
or undefined behavior may occur.
"""
lop_sf_fcc_builder_key = "LopSfFccBuilder"

class LopSfFccBuilder:
    def __init__(self)->None:
        return

    def __call__(self)->LopSfFcc:
        return LopSfFcc()

# ----------
# Private members
# ----------

def _main()->None:
    pass


if __name__ == "__main__":
    _main ()

