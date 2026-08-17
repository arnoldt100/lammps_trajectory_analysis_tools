"""Templates for a domain-neutral, key-based builder registry."""

from .builder_protocol import SupportsBuild
from .builder_registry import BuilderRegistry
from .exceptions import BuilderKeyError, BuilderRegistrationError

__all__ = [
    "BuilderKeyError",
    "BuilderRegistrationError",
    "BuilderRegistry",
    "SupportsBuild",
]
