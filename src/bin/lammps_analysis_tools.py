#! /usr/bin/env python3
""" The main program of this package.

This program calls other subprograms that do various
analysis, file conversions, etc.

"""

import argparse
import lammps_analysis_tool_parser
import create_ar_box_psf

def _create_parser()->argparse.ArgumentParser:
    """ Create a parser.

    Creates a parent parser. The the subparsers for each
    corresponding subcommand is added to the parent parser.
    """
    _parent_parser = lammps_analysis_tool_parser.parent_parser
    _parent_parser = \
            create_ar_box_psf.create_ar_box_psf_subparser(_parent_parser)
    return _parent_parser

def main ():
    parser : argparse.ArgumentParser = _create_parser()
    args = parser.parse_args()

    print ("Stud main LAMMPS tool program.")

if __name__ == "__main__":
    main()
