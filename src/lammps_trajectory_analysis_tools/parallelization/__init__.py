"""Parallel execution ownership and partitioning contracts."""

from .atom_assignment_protocol import AtomAssignmentProtocol
from .atom_thread_assignment import AtomThreadAssignment

__all__ = ["AtomAssignmentProtocol", "AtomThreadAssignment"]
