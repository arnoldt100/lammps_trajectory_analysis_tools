"""A domain-neutral, key-based registry of concrete builders."""

from typing import Any, Generic, TypeVar

from .builder_protocol import SupportsBuild
from .exceptions import BuilderKeyError, BuilderRegistrationError

P = TypeVar("P")


class BuilderRegistry(Generic[P]):
    """Maps string keys to concrete builders and builds products on demand.

    Each instance owns its own registrations; no state is shared between
    instances or hidden behind module-level globals.
    """

    def __init__(self) -> None:
        self._builders: dict[str, SupportsBuild[P]] = {}

    def register_builder(self, key: str, builder: SupportsBuild[P]) -> None:
        """Register ``builder`` under ``key``.

        Args:
            key: The unique identifier for the concrete builder.
            builder: A callable that constructs a product directly, i.e.
                ``builder(*args, **kwargs) -> Product``.

        Raises:
            BuilderRegistrationError: If ``key`` is already registered.
        """
        if key in self._builders:
            raise BuilderRegistrationError(f"builder already registered for key: {key}")
        self._builders[key] = builder

    def build(self, key: str, *args: Any, **kwargs: Any) -> P:
        """Build and return a product using the builder registered under ``key``.

        Args:
            key: The unique identifier of the concrete builder to invoke.
            *args: Positional arguments forwarded to the concrete builder.
            **kwargs: Keyword arguments forwarded to the concrete builder.

        Raises:
            BuilderKeyError: If no builder is registered under ``key``.
        """
        builder = self._builders.get(key)
        if builder is None:
            raise BuilderKeyError(key)
        return builder(*args, **kwargs)

    def has_builder(self, key: str) -> bool:
        """Return whether a builder is registered under ``key``."""
        return key in self._builders

    def keys(self) -> frozenset[str]:
        """Return the set of currently registered builder keys."""
        return frozenset(self._builders.keys())
