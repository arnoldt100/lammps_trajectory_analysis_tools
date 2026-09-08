import argparse

from typing import Any
from collections import OrderedDict

import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc import (
    subparser_builder_registry,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
    CLILopSfFcc,
)

# A dictionary of valid required command line options and options values.
_cli_required_arguments = OrderedDict( 
    [ ("lop_sf_fcc", None),
      ("--trajectory", "trajectory.dcd"),
      ("--psf", "topology.psf"),
      ("--edge-length" , "5.26"),
      ("--timeunits", "ps"),
      ("--dt", "0.01"),
      ("--cutoff", "4.5"),
      ("--md-params-json", "md.params.json"),
     ]
)

def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand_name")
    subparser_builder_registry.build("lop_sf_fcc", subparsers)
    return parser

def required_arguments() -> list[str]:
    args = []
    for option,value in _cli_required_arguments.items():
        args.append(option)
        if value is not None:
            args.append(value)
    return args

def modify_required_arguments(new_arguments : list[tuple[str, str]]) -> list[str]:
    """Modifies the required arguments based upon new_arguments. 

    New options are added to the end. Existing options are updated.

    Args:
        new_arguments: Takes the form of [(option1,value1), (option2, value2), ..., (optionN,valueN)]
    """
    temp_cli_required_arguments = _cli_required_arguments.copy()
    for option,value in new_arguments:
        temp_cli_required_arguments[option] = value

    args = []
    for option,value in temp_cli_required_arguments.items():
        args.append(option)
        if value is not None:
            args.append(value)
    return args

# Tests for option --parallel-threads option.
def test_parallel_threads_defaults_to_one() -> None:
    arguments = _create_parser().parse_args(required_arguments())

    assert CLILopSfFcc(**vars(arguments)).parallel_threads == 1


def test_parallel_threads_accepts_positive_integer() -> None:
    arguments = _create_parser().parse_args(
        required_arguments() + ["--parallel-threads", "4"]
    )
    assert CLILopSfFcc(**vars(arguments)).parallel_threads == 4


@pytest.mark.parametrize("value", ["0", "-1", "not-an-integer"])
def test_parallel_threads_rejects_invalid_cli_values(value: str) -> None:
    with pytest.raises(SystemExit):
        _create_parser().parse_args(
            required_arguments() + ["--parallel-threads", value]
        )


@pytest.mark.parametrize("value, exception", [(0, ValueError), (-1, ValueError), (True, TypeError), (1.5, TypeError)])
def test_cli_class_rejects_invalid_parallel_threads(
    value: object,
    exception: type[Exception],
) -> None:
    with pytest.raises(exception):
        CLILopSfFcc(parallel_threads=value)  # type: ignore[arg-type]

# Tests for option --md-params-json.
@pytest.mark.parametrize("value", ["", " ", None])
def test_md_params_json_rejects_invalid_cli_values(value: str) -> None:
    new_option_args = [("--md-params-json",value),]
    new_arguments = modify_required_arguments(new_option_args)
    with pytest.raises(SystemExit):
        arguments = _create_parser().parse_args(new_arguments)

def test_md_params_json_accepts_valid_cli_values() -> None:
    new_args = modify_required_arguments([("--md-params-json","json_file")])
    args1 = _create_parser().parse_args(new_args)
    assert CLILopSfFcc(**vars(args1)).md_params_json == "json_file"
