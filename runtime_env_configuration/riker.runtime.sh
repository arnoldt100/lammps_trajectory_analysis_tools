#! /usr/bin/env bash

# ---------------------------------------------------
# Define the environmental variable for the path
# to this project Riker's Python virtual environment.
# 
# ---------------------------------------------------
export LTAT_PYTHON_VENV="${AT_PYTHON_VENV}/riker-ltat-venv"

# ---------------------------------------------------
# Ensure that the core runtime file is sourced. This file
# file sets environmental variables that ar common across
# machines.
#
# ---------------------------------------------------
source "${LTAT_BUILD_CONFIG_ROOT}/core.env.sh"
