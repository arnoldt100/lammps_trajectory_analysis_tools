"""Protocol describing the common builder surface."""

from typing import Any, Protocol, TypeVar, runtime_checkable

P = TypeVar("P", covariant=True)


@runtime_checkable
class SupportsBuild(Protocol[P]):
    """A concrete builder: a callable that constructs a product directly."""

    def __call__(self, *args: Any, **kwargs: Any) -> P:
        """Construct and return a product from the given arguments."""
        ...
