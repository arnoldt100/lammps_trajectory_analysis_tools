#! /usr/bin/env python3

# Python standard library imports
from typing import Any

# Local library import 
from .LoopTimerBuilder import ( LoopTimerBuilder,
                                LoopTimerBuilderKey )

# ----------
# Public members
# ----------

class GeneralTimerBuilder:
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

timer_object_factory = GeneralTimerBuilder()
timer_object_factory.register_builder(LoopTimerBuilderKey ,LoopTimerBuilder)

# ----------
# Private members
# ----------

def _main()->None:
    return

if __name__ == "__main__":
    _main()
