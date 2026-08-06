#!/usr/bin/env bash

# ----------------------------------------------------
# The absolute path to the package top level directory
#
# This file must be sourced in top level of the workspace.
# ----------------------------------------------------
export LTAT_TOP_LEVEL="$(pwd)"

# ----------------------------------------------------
# The absolute path to the directory that contains the build configurations
#
# ----------------------------------------------------
export LTAT_BUILD_CONFIG_ROOT=${LTAT_TOP_LEVEL}/runtime_env_configuration

# ---------------------------------------------------
# Modify the PATH variable.
# ---------------------------------------------------
export PATH="${LTAT_TOP_LEVEL}/src/bin:${PATH}"

# ---------------------------------------------------
# Modify the PYTHONPATH variable.
# ---------------------------------------------------
export PYTHONPATH="$(pwd)/src:$(pwd)/tests:${PYTHONPATH}"

# ---------------------------------------------------
# Set the machine name.
#
# ---------------------------------------------------
export LTAT_MACHINE="NimzoIndian"

# ---------------------------------------------------
# Ensure that the environmental variable 'LTAT_BUILD_CONFIGURATION'
# is set and not null and the corresponding build configuration file exists.
#
# ---------------------------------------------------
if [[ ! ${LTAT_BUILD_CONFIGURATION:+LTAT_BUILD_CONFIGURATION} ]]; then
  echo 'Warning! The environmental variable LTAT_BUILD_CONFIGURATION is not set.'
  echo 'Please set to a valid value or the various analysis tools will fail.'
fi

if [[ ! -e "${LTAT_BUILD_CONFIG_ROOT}/${LTAT_BUILD_CONFIGURATION}" ]]; then
  echo "Warning! The build configuration file ${LTAT_BUILD_CONFIGURATION} doesn't exist."
  echo "According to the environment variables, the script is looking for the file at:"
  echo "${LTAT_BUILD_CONFIG_ROOT}/runtime_env_configuration/$LTAT_BUILD_CONFIGURATION"
  echo 'Please check your build configuration is in the correct directory.'
fi
export LTAT_BASH_BUILD_CONFIGURATION="${LTAT_BUILD_CONFIG_ROOT}/${LTAT_BUILD_CONFIGURATION}"
source ${LTAT_BASH_BUILD_CONFIGURATION}
