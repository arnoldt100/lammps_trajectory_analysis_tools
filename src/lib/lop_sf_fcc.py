#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""


""" A key that is uniquely associated with class LopSfFcc.

This key is used by other classes, especially builder classes, to register the
class LopSfFcc. These callable class each have a unique key or undefined
behavior may occur.
"""
key_lop_sf_fcc = '__lop_sf_fcc__'

class LopSfFcc:
    """ A callable that calculates a fcc local order parameter. """
    def __init__(self,*args,**kwarfs)->None:
        return

# ----------
# Private members
# ----------

def _main()->None:
    pass

if __name__ == "__main__":
    _main()

