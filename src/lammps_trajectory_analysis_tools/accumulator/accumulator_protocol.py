"""Protocol for worker-local accumulator implementations."""

from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class AccumulatorProtocol(Protocol[T]):
    """Describe the public contract for a worker-local accumulator.

    Implementations own local numerical storage and are used exclusively by
    one worker during accumulation. Reduction policy remains outside this
    protocol and belongs to a reducer implementation.
    """

    def accumulate(self, index: int, value: T) -> None:
        """Add a value associated with a global atom or property index."""
        ...

    def finalize(self) -> Any:
        """Return the accumulated result in public form."""
        ...

    def reset(self) -> None:
        """Clear accumulated values while preserving configuration."""
        ...

    @property
    def capacity(self) -> int:
        """Return the number of addressable result slots."""
        ...

    @property
    def dtype(self) -> Any:
        """Return the type of values stored by the accumulator."""
        ...
