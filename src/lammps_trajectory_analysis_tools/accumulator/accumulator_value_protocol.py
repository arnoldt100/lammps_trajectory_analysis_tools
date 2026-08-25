"""Protocol for immutable snapshots created from accumulators.

This is the value side of the accumulator contract. A mutable accumulator
implements :class:`AccumulatorProtocol`; its snapshot conversion, such as
``to_value()``, produces an independent object implementing this protocol.
"""

from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class AccumulatorValueProtocol(Protocol[T]):
    """Describe the immutable consumer side of the accumulator contract.

    An implementation represents a fixed snapshot of accumulated values and
    contribution counters. Its arrays are read-only, and observing the
    snapshot cannot change the mutable accumulator that produced it. This
    protocol is intended for reduction and result transfer, not for worker
    local accumulation; mutation operations such as ``accumulate()`` and
    ``reset()`` belong to :class:`AccumulatorProtocol`.
    """

    @property
    def values(self) -> Any:
        """Return the snapshot's read-only accumulated values."""
        ...

    @property
    def counters(self) -> Any:
        """Return the snapshot's read-only contribution counts."""
        ...

    @property
    def capacity(self) -> int:
        """Return the number of addressable result slots."""
        ...

    @property
    def dtype(self) -> Any:
        """Return the stored value dtype."""
        ...