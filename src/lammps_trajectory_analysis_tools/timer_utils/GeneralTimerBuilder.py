#! /usr/bin/env python3
""" <Brief Description>

<Detailed Description>

This module provides the following public members:
    <List of public members>
"""

# Python standard library imports
from typing import Any

# Local library import 
from .concrete_object_factory import ConcreteObjectFactory

# ----------
# Public members
# ----------

class GeneralObjectFactory:
    def __init__(self,*args,**kwargs)->None:
        self._builders = {}

    def register_builder(self, key, builder)->None:
        self._builders[key] = builder

    def create(self,key,*args, **kwargs)->Any:
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        my_builder = builder()
        return my_builder(*args,**kwargs)

concrete_object_factory = GeneralObjectFactory()
concrete_object_factory.register_builder('__concretefactorykey__',ConcreteObjectFactory)

# ----------
# Private members
# ----------

def _main()->None:
    return

if __name__ == "__main__":
    _main()
