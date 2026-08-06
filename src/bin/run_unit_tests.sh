#! /usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"
PYTHON_GIL=0 PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" uv run pytest -rA tests
