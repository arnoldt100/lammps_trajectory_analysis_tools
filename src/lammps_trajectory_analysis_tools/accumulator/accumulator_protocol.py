"""Protocol for mutable, worker-local accumulator implementations.

An implementation accumulates contributions into its private state and can
produce a read-only result. Implementations that need an immutable value for
reduction may additionally expose a conversion such as ``to_value()``; that
snapshot is described by :class:`AccumulatorValueProtocol`.
"""

from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class AccumulatorProtocol(Protocol[T]):
    """Describe the mutable producer side of the accumulator contract.

    Implementations own local numerical storage and are used exclusively by
    one worker during accumulation. ``accumulate()`` changes the worker-local
    state, ``reset()`` clears it, and ``finalize()`` exposes the current
    accumulated result for observation.

    An implementation may provide ``to_value()`` to create an independent
    immutable snapshot. Such snapshots implement
    :class:`AccumulatorValueProtocol` and are the appropriate inputs to a
    reducer. Reduction policy remains outside both protocols.
    """

    def accumulate(self, index: int, value: T) -> None:
        """Add a value associated with a global atom or property index."""
        ...

    def finalize(self) -> Any:
        """Return a read-only view of the current accumulated result.

        This observation result is not itself the immutable value protocol.
        Implementations that support immutable snapshots expose a separate
        conversion, such as ``to_value()``.
        """
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
