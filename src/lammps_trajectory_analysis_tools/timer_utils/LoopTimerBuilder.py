#! /usr/bin/env python3
""" The builder for the LoopTimer class


This module provides the following public members:
    LoopTimerBuilder
"""

# Python standard library imports

# Local library import
from .LoopTimer import LoopTimer

# ----------
# Public members
# ----------

class LoopTimerBuilder:
    def __init__(self,*args,**kwargs)->None:
        return

    def __call__(self,*kargs,**kwargs)->LoopTimer:
        return LoopTimer(*kargs,**kwargs)

def _main()->None:
    pass

# ----------
# Private members
# ----------

if __name__ == "__main__":
    _main ()

