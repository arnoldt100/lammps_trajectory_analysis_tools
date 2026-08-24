"""Protocol for immutable finalized accumulator values."""

from typing import Any, Protocol, TypeVar, runtime_checkable


T = TypeVar("T")


@runtime_checkable
class AccumulatorValueProtocol(Protocol[T]):
    """Describe read-only values produced by accumulator finalization."""

    @property
    def values(self) -> Any:
        """Return read-only accumulated values."""
        ...

    @property
    def counters(self) -> Any:
        """Return read-only contribution counts."""
        ...

    @property
    def capacity(self) -> int:
        """Return the number of addressable result slots."""
        ...

    @property
    def dtype(self) -> Any:
        """Return the stored value dtype."""
        ...