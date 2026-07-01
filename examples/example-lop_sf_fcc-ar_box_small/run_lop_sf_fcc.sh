#! /usr/bin/env bash

# Name of dcd file.
dcd_file=argon_box_small.dcd 

# Name of psf file.
psf_file=argon_box_small.psf

# ----------------------
# Argon force field settings.
# The force field parameters are from the following source:
#   Argon force field revisited: a molecular dynamic study
#   Journal of Physics Communications
#   José Guillermo Méndez-Bermúdez et al 2022 J. Phys. Commun. 6 041002
# See Table 2 for the Wh[2] force field.
# In the paper the reparameterized force field for Wh[2] is epsilon is
# 0.94639 KJ/mol and sigma is 0.33713 nm.
# 
# For the units real, distance is in angstroms and energy is in Kcal/mol. 
# We need to convert nm to angstroms and KJ/mol to Kcal/mol to use Wh[2]
# force field in this LAMMPS command file.
# 
# The fcc edge length is ~5.196 angstroms
# ----------------------

uv run  lammps_analysis_tool.py lop_sf_fcc --dcd-file-name argon_box_small.dcd  --psf argon_box_small.psf --edge-length 5.196
