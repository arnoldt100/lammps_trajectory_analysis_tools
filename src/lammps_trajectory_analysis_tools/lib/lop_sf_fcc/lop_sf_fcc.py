#! /usr/bin/env python3
""" This module contains the LopSfFcc class definition.

The public members provided by this module are:

    key_lop_sf_fcc : string
    LopSfFcc : A callable class
"""

# Python standard library imports
import os
import datetime
from pathlib import Path
from typing import Any

# Third party library imports
import numpy as np

# Local imports
from lammps_trajectory_analysis_tools.integrations.mdanalysis.universe import (
    load_universe,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
    CLILopSfFcc,
    create_mdanalysis_arguments,
)
from lammps_trajectory_analysis_tools.timer_utils import (
    LoopTimerBuilderKey,
    timer_object_factory,
)

from lammps_trajectory_analysis_tools.schemas import (
    read_json_file,
    validate_json_file,
)

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_mdanalysis import (
    LOP_SF_FCC, )

from lammps_trajectory_analysis_tools.lib.data_types import JSON

from lammps_trajectory_analysis_tools.data_writer_utils import (
    data_writer_factory,
    HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey
)

# ----------
# Public members
# ----------

""" A key that is uniquely associated with class LopSfFcc.

This key is used by other classes, especially builder classes, to register the
class LopSfFcc. These callable classes each have a unique key or undefined
behavior may occur. This key is currently not used but reserved for future use.
"""
key_lop_sf_fcc = 'LopSfFcc'

class LopSfFcc:
    """ A callable class that sets up and runs the LOP_SF_FCC analysis. """

    md_params_schema_filepath = os.path.join(os.getenv("LTAT_TOP_LEVEL"),
        "src","lammps_trajectory_analysis_tools","schemas",
        "md_params.schema.json")

    md_params_metadata_schema_filepath = os.path.join(os.getenv("LTAT_TOP_LEVEL"),
        "src","lammps_trajectory_analysis_tools","schemas",
        "md_metadata.schema.json")
    
    def __init__(self)->None:
        self._parallel_threads = 1

        # These attributes store the simulation parameters as a JSON
        # file and the corresponding JSON schema file for validation.
        self._md_params_json = None

        # These attributes store universe related data.
        self._universe = None
        self._nm_frames = None
        self._nm_atoms = None

        # These attributes are related to the neigbor search radius.
        self._neighbor_search_radius = None

        # These attributes are for writing results to hdf files.
        self._data_writer = None

        # The MDAnalysis analysis object that calculates and writes the FCC LOP.
        self._lop_sf_fcc = None

    def _set_attributes(self,command_line_arguments:CLILopSfFcc)->None:
        """ Sets the attributes of this class. """

        # Set the number of parallel threads.
        self._parallel_threads = command_line_arguments.parallel_threads

        # Set the JSON MD simulation atribute.
        self._md_params_json = (
            _set_md_params_attributes(command_line_arguments)
        )

        # Set the JSON MD simulation metadata atribute.
        self._md_metadata_json = (
            _set_md_params_metada_attributes(
                self._md_params_json["simulation_parameters"]["simulation_metadata"])
        )

        # Set the universe related attributes
        self._universe, self._nm_frames, self._nm_atoms = (
            _set_universe_attributes(command_line_arguments)
        )

        # Set the neighbor search radius.
        self._neighbor_search_radius = np.float32(command_line_arguments.cutoff)

        # Set the data writer attributes.
        self._data_writer = _set_data_writer_attributes(
                                command_line_arguments,
                                self._universe,
                                self._md_params_json,
                                self._md_metadata_json)

        # This attriribute is store the MDAnalysis ananlyis class to calculate the
        # local fcc order parameter.
        self._lop_sf_fcc = _set_lop_sf_fcc_attribute(
            self._universe.atoms,
            command_line_arguments.edge_length,
            self._neighbor_search_radius,
            self._data_writer)

    def __call__(self, command_line_arguments:CLILopSfFcc) -> Any:

        self._set_attributes(command_line_arguments)

        print(f"Number of trajectory frames = {self._nm_frames}")
        trajectory_loop_timer = (
            timer_object_factory.build(LoopTimerBuilderKey,"trajectory_loop",1,1)
        )
        trajectory_loop_timer.start()
        self._lop_sf_fcc.run(stop=self._nm_frames)
        trajectory_loop_timer.update(1)
        trajectory_loop_timer.stop()

        return

# ----------
# Private members
# ----------

def _set_data_writer_attributes(command_line_arguments:CLILopSfFcc,
                                universe,
                                md_params_json,
                                md_metadata_json)->None:
    hdf_file_name = command_line_arguments.output_hdf5_file

    layout_args = _build_layout_arguments(universe)
    metadata_args = _build_metadata_arguments(md_params_json,md_metadata_json)

    # Build the composite value object; no writer is opened yet.
    value_object = data_writer_factory.build(
        HDF5LopSfFccTrajectoryWriterValueObjectBuilderKey,
        file_path=Path(hdf_file_name),
        metadata=metadata_args,
        layout=layout_args,
    )

    return value_object

def _read_debug_plot_frames_env_var()->int | None:
    """ Returns the positive frame limit from LTAT_DEBUG_PLOT_FRAMES, or None
    if unset or non-positive (meaning: compute all frames).

    Raises:
        ValueError: If the env var is set but not a valid integer.
    """
    raw_value = os.environ.get("LTAT_DEBUG_PLOT_FRAMES")
    if raw_value is None:
        return None

    try:
        parsed_value = int(raw_value)
    except ValueError as error:
        raise ValueError(
            f"LTAT_DEBUG_PLOT_FRAMES must be an integer, got {raw_value!r}"
        ) from error

    if parsed_value <= 0:
        return None
    return parsed_value

def _resolve_nm_frames_to_compute(total_frames: int,
                                  debug_plot_frames: int | None)->int:
    """ Returns the number of trajectory frames to compute, honoring
    LTAT_DEBUG_PLOT_FRAMES if it requests fewer than total_frames.

    Raises:
        ValueError: If debug_plot_frames exceeds total_frames.
    """
    if debug_plot_frames is None:
        return total_frames

    if debug_plot_frames > total_frames:
        raise ValueError(
            f"LTAT_DEBUG_PLOT_FRAMES={debug_plot_frames} exceeds the "
            f"number of available trajectory frames ({total_frames})"
        )
    return debug_plot_frames

def _set_universe_attributes(command_line_arguments:CLILopSfFcc)->tuple[Any,...]:
    my_positional_args,my_keyword_args = create_mdanalysis_arguments(command_line_arguments)
    my_universe = load_universe(my_positional_args["topology_path"],
                                my_positional_args["trajectory_source"],
                                **my_keyword_args)

    # Loop over each trajectory and calculate the lop fcc fcc
    total_nm_frames = my_universe.trajectory.n_frames
    debug_plot_frames = _read_debug_plot_frames_env_var()
    nm_frames = _resolve_nm_frames_to_compute(total_nm_frames, debug_plot_frames)
    nm_atoms = my_universe.atoms.n_atoms
    return my_universe, nm_frames, nm_atoms 

def _set_md_params_attributes(
        command_line_arguments:CLILopSfFcc)->JSON:

    # We read the JSON file for the simulation parameters.
    validate_json_file(command_line_arguments.md_params_json,
                       LopSfFcc.md_params_schema_filepath)
    md_params_json = read_json_file(command_line_arguments.md_params_json)
    return md_params_json

def _set_md_params_metada_attributes(
        md_simulation_metadata_filepath:str)->JSON:

    # We read the JSON file for the simulation parameters.
    validate_json_file(md_simulation_metadata_filepath,
                       LopSfFcc.md_params_metadata_schema_filepath)
    md_metadata_json = read_json_file(md_simulation_metadata_filepath)
    return md_metadata_json

def _build_layout_arguments(universe)->dict[str,Any]:
    nm_atoms = universe.atoms.n_atoms
    length_units_label = universe.trajectory.units["length"]
    layout_arguments = {"number_of_atoms" : nm_atoms,
                        "length_units_label" : length_units_label}
    return layout_arguments

def _set_lop_sf_fcc_attribute(atom_group, edge_length, cutoff, data_writer):
    return LOP_SF_FCC(atom_group, edge_length, cutoff, data_writer=data_writer)

def _build_metadata_arguments(md_params_json:JSON,
                              md_metadata_json:JSON ):
    metadata_args = {}
    metadata_args["time_units_label"] = (
        md_params_json["simulation_parameters"]["time"]["units"]
    )

    metadata_args["time_step"] = (
        md_params_json["simulation_parameters"]["time"]["time_step"]
    )

    metadata_args["number_of_trajectories"] = (
        md_params_json["simulation_parameters"]["time"]["total_steps"]
    )

    metadata_args["generation_date"] = (
        datetime.datetime.fromisoformat(md_params_json["simulation_parameters"]["date"])
    )

    metadata_args["compiler_build_flags"] = (
       md_metadata_json["simulation_metadata"]["build_description"]["compiler_flags"]
    )

    metadata_args["generating_machine"] = (
        md_metadata_json["simulation_metadata"]["build_description"]["compiling_machine"]
    )

    metadata_args["lmod_modules"] = (
        md_metadata_json["simulation_metadata"]["build_description"]["programming_environment"]
    )
    return metadata_args

def _main()->None:
    pass

if __name__ == "__main__":
    _main()

