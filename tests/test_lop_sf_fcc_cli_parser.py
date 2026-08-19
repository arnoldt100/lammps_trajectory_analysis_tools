import argparse

import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.lop_sf_fcc_cli_parser import (
    CLILopSfFcc,
    LopSfFccSubparserFactory,
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand_name")
    LopSfFccSubparserFactory()(subparsers)
    return parser


def required_arguments() -> list[str]:
    return [
        "lop_sf_fcc",
        "--trajectory",
        "trajectory.dcd",
        "--psf",
        "topology.psf",
        "--edge-length",
        "5.26",
        "--timeunits",
        "ps",
        "--dt",
        "0.01",
        "--cutoff",
        "4.5",
    ]


def test_parallel_threads_defaults_to_one() -> None:
    arguments = create_parser().parse_args(required_arguments())

    assert CLILopSfFcc(**vars(arguments)).parallel_threads == 1


def test_parallel_threads_accepts_positive_integer() -> None:
    arguments = create_parser().parse_args(
        required_arguments() + ["--parallel-threads", "4"]
    )

    assert CLILopSfFcc(**vars(arguments)).parallel_threads == 4


@pytest.mark.parametrize("value", ["0", "-1", "not-an-integer"])
def test_parallel_threads_rejects_invalid_cli_values(value: str) -> None:
    with pytest.raises(SystemExit):
        create_parser().parse_args(
            required_arguments() + ["--parallel-threads", value]
        )


@pytest.mark.parametrize("value, exception", [(0, ValueError), (-1, ValueError), (True, TypeError), (1.5, TypeError)])
def test_cli_class_rejects_invalid_parallel_threads(
    value: object,
    exception: type[Exception],
) -> None:
    with pytest.raises(exception):
        CLILopSfFcc(parallel_threads=value)  # type: ignore[arg-type]
