"""Compatibility name for the shared builder registry."""

from lammps_trajectory_analysis_tools.design_patterns_templates.builder import (
    BuilderRegistry,
)

GeneralTimerBuilder = BuilderRegistry

# ----------
# Private members
# ----------

def _main() -> None:
    return

if __name__ == "__main__":
    _main()
