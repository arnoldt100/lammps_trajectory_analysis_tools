"""Exceptions raised at the data-writer contract boundary."""


class DataWriterError(Exception):
    """Base class for data-writer failures."""


class DataWriterConfigurationError(DataWriterError, ValueError):
    """Raised when writer configuration or input data is invalid."""


class DataWriterLifecycleError(DataWriterError, RuntimeError):
    """Raised when a writer operation is invalid for its current lifecycle."""


class DataWriterTargetError(DataWriterError, OSError):
    """Raised when the output target cannot be created or written."""