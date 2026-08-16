from pathlib import Path

import h5py
import numpy as np
import pytest

from lammps_trajectory_analysis_tools.data_writer_utils import (
    DataWriterConfigurationError,
    DataWriterLifecycleError,
    DataWriterProtocol,
)
from lammps_trajectory_analysis_tools.data_writer_utils.hdf5_data_writer import (
    HDF5DataWriter,
)


@pytest.fixture
def writer(tmp_path: Path) -> HDF5DataWriter:
    return HDF5DataWriter(tmp_path / "data.h5", "frames", (2,), "float64")


def test_hdf5_writer_follows_protocol_and_writes_complete_data(
    writer: HDF5DataWriter,
) -> None:
    assert isinstance(writer, DataWriterProtocol)
    data = np.array([[1.0, 2.0], [3.0, 4.0]])

    writer.create()
    writer.write_data(data)
    writer.close()

    with h5py.File(writer.configuration["file_path"], "r") as output:
        np.testing.assert_array_equal(output["frames"], data)


def test_create_initializes_empty_stream_and_write_replaces_contents(
    writer: HDF5DataWriter,
) -> None:
    writer.create()
    with h5py.File(writer.configuration["file_path"], "r") as output:
        assert output["frames"].shape == (0, 2)

    writer.write_data(np.array([[1.0, 2.0], [3.0, 4.0]]))
    writer.write_data(np.array([[9.0, 8.0]]))
    writer.close()

    with h5py.File(writer.configuration["file_path"], "r") as output:
        np.testing.assert_array_equal(output["frames"], np.array([[9.0, 8.0]]))


def test_append_preserves_order_for_single_and_batch_frames(
    writer: HDF5DataWriter,
) -> None:
    writer.create()
    writer.append_data(np.array([1.0, 2.0]))
    writer.append_data(np.array([[3.0, 4.0], [5.0, 6.0]]))
    writer.close()

    with h5py.File(writer.configuration["file_path"], "r") as output:
        np.testing.assert_array_equal(
            output["frames"], np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        )


def test_invalid_append_does_not_modify_existing_frames(
    writer: HDF5DataWriter,
) -> None:
    writer.create()
    writer.append_data(np.array([[1.0, 2.0]]))

    with pytest.raises(DataWriterConfigurationError):
        writer.append_data(np.array([[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]]))

    writer.close()
    with h5py.File(writer.configuration["file_path"], "r") as output:
        np.testing.assert_array_equal(output["frames"], np.array([[1.0, 2.0]]))


def test_incompatible_type_is_rejected_before_append(writer: HDF5DataWriter) -> None:
    writer.create()
    with pytest.raises(DataWriterConfigurationError, match="cannot be safely cast"):
        writer.append_data(np.array([[1.0 + 2.0j, 3.0 + 4.0j]]))
    writer.close()


def test_write_before_create_and_after_close_raise_lifecycle_error(
    writer: HDF5DataWriter,
) -> None:
    with pytest.raises(DataWriterLifecycleError):
        writer.write_data(np.array([[1.0, 2.0]]))

    writer.create()
    writer.close()
    with pytest.raises(DataWriterLifecycleError):
        writer.append_data(np.array([1.0, 2.0]))