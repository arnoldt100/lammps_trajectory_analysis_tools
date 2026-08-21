import pytest

from lammps_trajectory_analysis_tools.design_patterns_templates.value_semantics.validation import (
    ValueValidationError,
    validate_state,
)


def test_validate_state_runs_cross_field_validators():
    def validate_range(state):
        if state["low"] > state["high"]:
            raise ValueError("low must not exceed high")

    validate_state(
        {"low": 1, "high": 2},
        validators=(validate_range,),
    )

    with pytest.raises(ValueValidationError, match="low must not exceed high"):
        validate_state(
            {"low": 3, "high": 2},
            validators=(validate_range,),
        )


def test_validate_state_accepts_arbitrary_state_without_mapping_requirements():
    validate_state(10)
