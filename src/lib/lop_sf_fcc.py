#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
from typing import Any

# ----------
# Public members
# ----------

""" A key that is uniquely associated with class LopSfFcc.

This key is used by other classes, especially builder classes, to register the
class LopSfFcc. These callable classes each have a unique key or undefined
behavior may occur.
"""
key_lop_sf_fcc = 'LopSfFcc'

class LopSfFcc:
    """ A callable class that calculates a fcc local order parameter. """
    def __init__(self,*args,**kwargs)->None:
        return

    def __call__(self, command_line_arguments, *args: Any, **kwargs: Any) -> Any:
        print("Stud call LopSfFcc::__call__ for calculating fcc structure factor.")
        print(command_line_arguments)

        # Read the dcd file using MDAnalysis

        # Loop over every frame in the dcd trajectory, compute
        # every atoms local order parameter. We acccumulate the lop values 



# ----------
# Private members
# ----------

def _main()->None:
    pass

if __name__ == "__main__":
    _main()

