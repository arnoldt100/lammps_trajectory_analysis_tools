"""Backend-neutral protocol for data writers."""

from collections.abc import Mapping
from typing import Any, Protocol, Self, runtime_checkable


@runtime_checkable
class DataWriterProtocol(Protocol):
    """Contract for writers that persist complete data and ordered frames."""

    @property
    def configuration(self) -> Mapping[str, Any]:
        """Return the immutable writer configuration."""
        ...

    def create(self) -> None:
        """Create or replace the output target and initialize an empty stream."""
        ...

    def write_data(self, data: Any) -> None:
        """Replace the stream with one complete dataset."""
        ...

    def append_data(self, frames: Any) -> None:
        """Append one frame or a batch of frames in input order."""
        ...

    def close(self) -> None:
        """Finalize writes and release backend resources."""
        ...

    def __enter__(self) -> Self:
        """Return the writer for context-manager use."""
        ...

    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
        """Close the writer when leaving a context."""
        ...