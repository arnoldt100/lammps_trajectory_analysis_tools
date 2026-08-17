"""Exceptions raised by the builder-registry template."""


class BuilderKeyError(KeyError):
    """Raised when ``build`` is called with an unregistered key."""


class BuilderRegistrationError(ValueError):
    """Raised when ``register_builder`` is called with an already-registered key."""
