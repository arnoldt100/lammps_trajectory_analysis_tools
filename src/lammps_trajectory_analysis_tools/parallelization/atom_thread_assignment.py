"""Immutable deterministic assignments of atoms to worker threads."""

from collections.abc import Iterable, Sequence
from operator import index as as_index

import numpy as np

from .atom_assignment_protocol import AtomAssignmentProtocol


class AtomThreadAssignment(AtomAssignmentProtocol):
    """Store a validated, read-only assignment of global atom indices."""

    def __init__(
        self,
        atom_count: int,
        thread_count: int,
        assignments: Sequence[Iterable[int]],
    ) -> None:
        """Create an assignment after validating complete atom ownership."""
        self._atom_count = self._validate_non_negative(atom_count, "atom_count")
        self._thread_count = self._validate_positive(thread_count, "thread_count")
        self._assignments = self._normalize_assignments(assignments)
        self._owners = self._create_owner_index()

    @classmethod
    def from_balanced_partition(
        cls,
        atom_count: int,
        thread_count: int,
    ) -> AtomThreadAssignment:
        """Create a deterministic contiguous balanced atom partition."""
        atom_count = cls._validate_non_negative(atom_count, "atom_count")
        thread_count = cls._validate_positive(thread_count, "thread_count")
        base_size, remainder = divmod(atom_count, thread_count)
        assignments: list[np.ndarray] = []
        start = 0
        for thread_index in range(thread_count):
            size = base_size + (thread_index < remainder)
            stop = start + size
            assignments.append(np.arange(start, stop, dtype=np.int64))
            start = stop
        return cls(atom_count, thread_count, assignments)

    @staticmethod
    def _validate_non_negative(value: int, name: str) -> int:
        """Validate and normalize a non-negative integer."""
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        try:
            normalized_value = as_index(value)
        except TypeError as error:
            raise TypeError(f"{name} must be an integer") from error
        if normalized_value < 0:
            raise ValueError(f"{name} must be non-negative")
        return normalized_value

    @staticmethod
    def _validate_positive(value: int, name: str) -> int:
        """Validate and normalize a positive integer."""
        normalized_value = AtomThreadAssignment._validate_non_negative(value, name)
        if normalized_value == 0:
            raise ValueError(f"{name} must be positive")
        return normalized_value

    def _normalize_assignments(
        self,
        assignments: Sequence[Iterable[int]],
    ) -> tuple[np.ndarray, ...]:
        """Copy, validate, and freeze each thread assignment array."""
        if len(assignments) != self._thread_count:
            raise ValueError("assignment count must equal thread_count")

        normalized: list[np.ndarray] = []
        flattened: list[int] = []
        for thread_atoms in assignments:
            atom_array = np.asarray(tuple(thread_atoms), dtype=np.int64)
            if atom_array.ndim != 1:
                raise ValueError("each thread assignment must be one-dimensional")
            if np.any(atom_array < 0) or np.any(atom_array >= self._atom_count):
                raise ValueError("atom index is outside the valid range")
            atom_array = atom_array.copy()
            atom_array.flags.writeable = False
            normalized.append(atom_array)
            flattened.extend(int(atom_index) for atom_index in atom_array)

        if len(set(flattened)) != len(flattened):
            raise ValueError("an atom index is assigned to multiple threads")
        if len(flattened) != self._atom_count:
            raise ValueError("each atom must have exactly one assignment")
        if set(flattened) != set(range(self._atom_count)):
            raise ValueError("atom assignments must cover every atom index")
        return tuple(normalized)

    def _create_owner_index(self) -> np.ndarray:
        """Create a read-only global atom-to-thread lookup array."""
        owners = np.empty(self._atom_count, dtype=np.int64)
        for thread_index, atom_indices in enumerate(self._assignments):
            owners[atom_indices] = thread_index
        owners.flags.writeable = False
        return owners

    @property
    def thread_count(self) -> int:
        """Return the number of thread assignments."""
        return self._thread_count

    @property
    def atom_count(self) -> int:
        """Return the total number of atoms."""
        return self._atom_count

    @property
    def assignments(self) -> tuple[np.ndarray, ...]:
        """Return read-only assignment arrays ordered by thread index."""
        return tuple(atom_indices.view() for atom_indices in self._assignments)

    def atoms_for_thread(self, thread_index: int) -> np.ndarray:
        """Return a read-only array of atoms assigned to one thread."""
        if not 0 <= thread_index < self._thread_count:
            raise IndexError("thread_index is outside the valid range")
        return self._assignments[thread_index].view()

    def owner_of_atom(self, atom_index: int) -> int:
        """Return the unique thread owning an atom index."""
        if not 0 <= atom_index < self._atom_count:
            raise IndexError("atom_index is outside the valid range")
        return int(self._owners[atom_index])
