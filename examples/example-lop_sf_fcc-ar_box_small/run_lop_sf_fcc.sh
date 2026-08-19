#! /usr/bin/env bash

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
# For the LAMMPS units real, distance is in angstroms and energy is in Kcal/mol.
# We need to convert nm to angstroms and KJ/mol to Kcal/mol to use Wh[2]
# force field in a LAMMPS command file.
#
# The fcc edge length for argon is ~5.196 angstroms for a lj 12-6 potential
# with sigma of 0.33713 nm.
#
# The original DCD file contains 5,849 atoms was split
# with the command
#
#   split -d -b 50M argon_box_small.dcd argon_box_small_dcd_
#
# We split the original DCD file to avoid the large file size restriction for git
# repositories. GitHub sets their restriction to file sizes < 100MB.
#
# We reform the original DCD file with the command
#
#   cat argon_box_small_dcd_* > ${dcd_file}
#
# ----------------------

# Name of DCD file.
dcd_file=argon_box_small.dcd

# Name of PSF file.
psf_file=argon_box_small.psf

# Name of the output hdf5 file
output_hdf5=ar_box_small.lop_sf_fcc.hdf5

# The edge length in angstroms.
edge_length=5.196

# The time units is emtoseconds
timeunits="ps"

# The time frame interval is 1 ps
dt=1.0

# The cutoff distance in angstroms for the neighbore search.
cutoff=10.4

# Define the number of parallel threads.
nm_threads=2

# Reform the original DCD file.
cat argon_box_small_dcd_* >${dcd_file}

# Run the example.
uv run lammps_analysis_tool.py lop_sf_fcc --trajectory argon_box_small.dcd \
  --psf argon_box_small.psf --edge-length 5.19 --timeunits ${timeunits} --dt ${dt} \
  --cutoff ${cutoff} --output-hdf5-file ${output_hdf5} \
  --parallel-threads=${nm_threads}
