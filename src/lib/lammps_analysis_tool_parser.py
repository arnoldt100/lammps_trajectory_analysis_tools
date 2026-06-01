"""  This module 

"""

import argparse
import create_ar_box_psf

# Create a  parent parser.
parent_parser : argparse.ArgumentParser = \
        argparse.ArgumentParser(prog="lammps_analysis_tool_parser",
                                description="Calculates various physical properties of LAMMPS simulations")
