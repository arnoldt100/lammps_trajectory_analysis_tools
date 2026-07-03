#! /usr/bin/env python3

# Python standard library imports
from typing import Any

# Local library import
from lop_sf_fcc.lop_sf_fcc_builder import key_lop_sf_fcc_factory
from lop_sf_fcc.lop_sf_fcc_builder import LopSfFccFactory

# ----------
# Public members
# ----------
class GeneralLammpsAnalysisToolFactory:
    def __init__(self,*args,**kwargs)->None:
        self._builders = {}

    def register_builder(self, key, builder)->None:
        self._builders[key] = builder

    def create(self,key,*args:Any, **kwargs: Any)->Any:
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        my_builder = builder()
        return my_builder(*args,**kwargs)

analysis_tool_factory = GeneralLammpsAnalysisToolFactory()
analysis_tool_factory.register_builder(key_lop_sf_fcc_factory,LopSfFccFactory)

# ----------
# Private members
# ----------

def _main()->None:
    pass


if __name__ == "__main__":
    _main ()
