#! /usr/bin/env bash
unset PYTHON_GIL

# The command 'uv run' can locate the Python virtual environment if the
# environmental variable 'UV_PROJECT_ENVIRONMENT' is set to 'LTAT_PYTHON_VENV'.
export UV_PROJECT_ENVIRONMENT="${LTAT_PYTHON_VENV}"

