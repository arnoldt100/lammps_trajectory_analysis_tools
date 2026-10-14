#! /usr/bin/env python3

"""Convert the bundled LOP SF FCC trajectory to a VTKHDF animation."""

from pathlib import Path

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc_vtkhdf_writer import (
    convert_hdf5_lop_sf_fcc_to_vtkhdf,
)


def main() -> None:
    """Convert the example HDF5 trajectory into a VTKHDF animation file."""
    example_directory = Path(__file__).resolve().parent
    source_path = (
        example_directory
        / "ar_box_small.lop_sf_fcc.nm-frames-1.validated.hdf5"
    )
    target_path = example_directory / "ar_box_small.lop_sf_fcc.animation.vtkhdf"

    output_path = convert_hdf5_lop_sf_fcc_to_vtkhdf(source_path, target_path)
    print(f"Created VTKHDF animation: {output_path}")


if __name__ == "__main__":
    main()
