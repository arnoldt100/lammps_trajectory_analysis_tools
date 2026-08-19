"""Protocols for immutable atom-to-thread assignments."""

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class AtomAssignmentProtocol(Protocol):
    """Describe a read-only mapping from threads to global atom indices."""

    @property
    def thread_count(self) -> int:
        """Return the number of thread assignments."""
        ...

    @property
    def atom_count(self) -> int:
        """Return the total number of atoms."""
        ...

    @property
    def assignments(self) -> tuple[np.ndarray, ...]:
        """Return read-only one-dimensional arrays by thread index."""
        ...

    def atoms_for_thread(self, thread_index: int) -> np.ndarray:
        """Return the read-only atom indices assigned to one thread."""
        ...

    def owner_of_atom(self, atom_index: int) -> int:
        """Return the unique owning thread for an atom."""
        ...
