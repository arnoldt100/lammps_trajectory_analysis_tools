#! /usr/bin/env bash
export PYTHON_GIL=0

# Define the path to the Python .venv directory.
export LTAT_PYTHON_VENV=${LTAT_TOP_LEVEL}/.venv

# The command 'uv run' can locate the Pyhton virtual environment if the
# environmental variable 'VIRTUAL_ENV' is set to 'LTAT_PYTHON_VENV'.
#
# export VIRTUAL_ENV=${LTAT_PYTHON_VENV}
