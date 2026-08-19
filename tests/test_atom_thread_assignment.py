import numpy as np
import pytest

from lammps_trajectory_analysis_tools.parallelization import (
    AtomAssignmentProtocol,
    AtomThreadAssignment,
)


def test_balanced_partition_is_deterministic_and_complete() -> None:
    assignment = AtomThreadAssignment.from_balanced_partition(10, 3)

    assert isinstance(assignment, AtomAssignmentProtocol)
    assert [values.tolist() for values in assignment.assignments] == [
        [0, 1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    assert assignment.atom_count == 10
    assert assignment.thread_count == 3
    assert [assignment.owner_of_atom(index) for index in range(10)] == [
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        2,
        2,
        2,
    ]


def test_more_threads_than_atoms_creates_empty_read_only_assignments() -> None:
    assignment = AtomThreadAssignment.from_balanced_partition(2, 4)

    assert [values.tolist() for values in assignment.assignments] == [[0], [1], [], []]
    assert all(values.ndim == 1 for values in assignment.assignments)
    assert all(values.dtype == np.int64 for values in assignment.assignments)
    assert all(not values.flags.writeable for values in assignment.assignments)
    assert assignment.atoms_for_thread(3).size == 0


def test_invalid_thread_index_raises_index_error() -> None:
    assignment = AtomThreadAssignment.from_balanced_partition(2, 1)

    with pytest.raises(IndexError):
        assignment.atoms_for_thread(1)


def test_duplicate_atom_assignment_is_rejected() -> None:
    with pytest.raises(ValueError, match="multiple threads"):
        AtomThreadAssignment(2, 2, ((0,), (0, 1)))


def test_incomplete_atom_assignment_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly one assignment"):
        AtomThreadAssignment(2, 2, ((0,), ()))


def test_out_of_range_atom_assignment_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside the valid range"):
        AtomThreadAssignment(2, 1, ((0, 2),))
