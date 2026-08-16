#! /usr/bin/env python3
""" This module provides a class for writing data to HDF5 files.

This module provides the following public members:
    HDF5DataWriter: A class for writing data to HDF5 files.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from lammps_trajectory_analysis_tools.data_writer_utils.exceptions import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterTargetError,
)

# ----------
# Public members
# ----------
class HDF5DataWriter:
    """Write complete datasets or ordered frames to an HDF5 dataset.

    ``create`` replaces an existing file. The configured shape describes one
    frame, and the HDF5 dataset stores frames along a new leading axis.
    """

    def __init__(
        self,
        file_path: str | Path,
        dataset_name: str,
        data_shape: tuple[int, ...],
        data_type: str,
    ) -> None:
        """
        Initializes the HDF5DataWriter instance.

        Args:
            file_path (str): The path to the HDF5 file.
            dataset_name (str): The name of the dataset to write to.
            data_shape (tuple): The shape of the data to be written.
            data_type (str): The data type of the dataset.
        """
        if not dataset_name:
            raise DataWriterConfigurationError("dataset_name must not be empty")
        if any(dimension < 0 for dimension in data_shape):
            raise DataWriterConfigurationError("data_shape dimensions must be non-negative")
        try:
            self._data_type = np.dtype(data_type)
        except TypeError as error:
            raise DataWriterConfigurationError(f"invalid data_type: {data_type}") from error
        self._file_path = Path(file_path)
        self._dataset_name = dataset_name
        self._data_shape = tuple(data_shape)
        self._file: h5py.File | None = None

    @property
    def configuration(self) -> Mapping[str, Any]:
        """Return the configured output target and stream details."""
        return {
            "file_path": self._file_path,
            "dataset_name": self._dataset_name,
            "frame_shape": self._data_shape,
            "data_type": str(self._data_type),
        }

    def create(self) -> None:
        """Create or replace the file and initialize an empty frame stream."""
        self.close()
        try:
            self._file = h5py.File(self._file_path, "w")
            self._file.create_dataset(
                self._dataset_name,
                shape=(0, *self._data_shape),
                maxshape=(None, *self._data_shape),
                dtype=self._data_type,
            )
        except (OSError, TypeError, ValueError) as error:
            self.close()
            raise DataWriterTargetError(
                f"could not create HDF5 target '{self._file_path}'"
            ) from error

    def create_data_file(self) -> None:
        """
        Creates an HDF5 file and initializes the dataset.

        This method creates an HDF5 file at the specified file path and
        initializes a dataset with the given name, shape, and data type.
        """
        self.create()
    
    def write_data(self, data: Any) -> None:
        """
        Writes data to the specified HDF5 dataset.

        Args:
            data: The data to be written to the dataset.
        """
        dataset = self._require_dataset()
        values = self._validated_values(data, complete_data=True)
        dataset.resize((values.shape[0], *self._data_shape))
        dataset[...] = values

    def append_data(self, frames: Any) -> None:
        """Append one frame or a batch of frames without partial updates."""
        dataset = self._require_dataset()
        values = self._validated_values(frames, complete_data=False)
        old_count = dataset.shape[0]
        dataset.resize((old_count + values.shape[0], *self._data_shape))
        dataset[old_count:] = values

    def close(self) -> None:
        """
        Closes the HDF5 file.

        This method should be called after all data has been written to
        ensure that the file is properly closed and resources are released.
        """
        if self._file is not None:
            self._file.close()
            self._file = None

    def close_file(self) -> None:
        """Close the HDF5 file; retained as a compatibility alias."""
        self.close()

    def __enter__(self) -> "HDF5DataWriter":
        """Create the target and return this writer."""
        self.create()
        return self

    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
        """Close the target when leaving a context."""
        self.close()

    def _require_dataset(self) -> h5py.Dataset:
        if self._file is None or not self._file.id.valid:
            raise DataWriterLifecycleError("writer must be created before writing")
        return self._file[self._dataset_name]

    def _validated_values(self, data: Any, *, complete_data: bool) -> np.ndarray:
        values = np.asarray(data)
        frame_rank = len(self._data_shape)
        valid_ranks = (frame_rank + 1,) if complete_data else (frame_rank, frame_rank + 1)
        if values.ndim not in valid_ranks:
            raise DataWriterConfigurationError(
                f"data rank {values.ndim} is incompatible with frame shape {self._data_shape}"
            )
        if complete_data:
            frame_values = values
            if values.shape[1:] != self._data_shape:
                raise DataWriterConfigurationError(
                    f"data shape {values.shape} does not match frame shape {self._data_shape}"
                )
        else:
            frame_values = (
                values.reshape((1, *values.shape))
                if values.shape == self._data_shape
                else values
            )
            if frame_values.shape[1:] != self._data_shape:
                raise DataWriterConfigurationError(
                    f"frame shape {values.shape} does not match {self._data_shape}"
                )
        if not np.can_cast(values.dtype, self._data_type, casting="safe"):
            raise DataWriterConfigurationError(
                f"data type {values.dtype} cannot be safely cast to {self._data_type}"
            )
        return frame_values.astype(self._data_type, copy=False)

# ----------
# Private members
# ----------

def _main()->None:
    return

if __name__ == "__main__":
    _main()
