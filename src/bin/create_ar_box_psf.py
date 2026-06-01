#! /usr/bin/env python3
""" Creates a Protein Structure File for a box of Argon Atoms.
"""

import argparse

def create_ar_box_psf():
    print ("Stud program to create PSF file.")

def create_ar_box_psf_subparser(parent_parser : argparse.ArgumentParser) -> argparse.ArgumentParser:
    """ Adds a subparser to the parent parser.

    The subparser is for the subcommand "create_ar_box_psf".
    """
    return parent_parser

