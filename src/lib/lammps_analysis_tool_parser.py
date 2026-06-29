"""  This module creates the parsers for the command line arguments.

Each tool corresponds to a subcommand that has its own command line arguments.
This module has the responsibility of adding the subparsers for each subcommand.

We use a factory or builder pattern where each subcommand has a concrete builder
that adds the appropiates options, help messages, etc. 

(1) Create a concrete object that adds the approiate options for the tool
(2) Instatiate a "general object factory".
(3) Register the 'concrete object' with the general object factory.
(3) Via the "general object factory" build for each subcommand the final Lammps Analysis Tool Parser.

"""

import argparse

class _ConcreteObject:
    def __init__(self,*args,**kwarfs)->None:
        return

class _ConcreteObjectFactory:
    def __init__(self,*args,**kwargs)->None:
        return

    def __call__(self,*kargs,**kwargs)->ConcreteObject:
        return _ConcreteObject(*kargs,**kwargs)

class _GeneralObjectFactory:
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


my_parser = argparse.ArgumentParser(prog="lammps_analysis_tool_parser",
                                    description="Calculates various physical properties of LAMMPS simulations")

concrete_object_factory = GeneralObjectFactory()

# Register the 

concrete_object_factory.register_builder('__concretefactorykey__',ConcreteObjectFactory)
