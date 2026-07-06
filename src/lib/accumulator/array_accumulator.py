#! /usr/bin/env python3
""" Defines a bounded accumulator designed for a fixed sequence of elements.

"""

# Python standard library imports
from typing import TypeVar, Generic

# Local Library package imports

T = TypeVar('T')

class GenericFixedSizedAccumulator(Generic[T]):
    def __init__(self, size: int):
        self._items = []


# ----------
# Public members
# ----------

def _main()->None:
    return

if __name__ == "__main__":
    _main()
