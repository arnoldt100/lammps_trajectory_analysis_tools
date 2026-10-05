from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter import (
    LopSfFccXdmfExporter,
    PlotterConfigurationError,
)
from lammps_trajectory_analysis_tools.lib.lop_sf_fcc.visit_plotter.lop_sf_fcc_series_exporter import (
    SPATIAL_DIMENSION,
)

from .conftest import NM_ATOMS, NM_FRAMES


def test_export_writes_well_formed_temporal_collection(
    lop_hdf5_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "series.xdmf"
    written = LopSfFccXdmfExporter(lop_hdf5_path).export(output)

    assert written == output
    assert output.is_file()
    root = ET.fromstring(output.read_text())
    assert root.tag == "Xdmf"

    collections = root.findall(
        './Domain/Grid[@GridType="Collection"][@CollectionType="Temporal"]'
    )
    assert len(collections) == 1
    frames = collections[0].findall('Grid[@GridType="Uniform"]')
    assert len(frames) == NM_FRAMES


def test_each_frame_references_positions_and_lop_in_place(
    lop_hdf5_path: Path, tmp_path: Path
) -> None:
    output = LopSfFccXdmfExporter(lop_hdf5_path).export(tmp_path / "s.xdmf")
    root = ET.fromstring(output.read_text())
    frames = root.findall('./Domain/Grid/Grid[@GridType="Uniform"]')
    source = lop_hdf5_path.resolve().as_posix()

    for index, frame in enumerate(frames):
        time = frame.find("Time")
        assert time is not None
        assert float(time.get("Value")) == pytest.approx(index * 0.002)

        topology = frame.find("Topology")
        assert topology.get("TopologyType") == "PolyVertex"
        assert int(topology.get("NumberOfElements")) == NM_ATOMS

        geometry_item = frame.find("./Geometry/DataItem")
        assert geometry_item is not None
        assert geometry_item.get("Format") == "HDF"
        assert geometry_item.get("Dimensions") == f"{NM_ATOMS} {SPATIAL_DIMENSION}"
        assert source in geometry_item.text
        assert f"traj_{index:05d}/positions" in geometry_item.text

        attribute = frame.find('Attribute[@AttributeType="Scalar"]')
        assert attribute.get("Name") == "lop_sf_fcc"
        assert attribute.get("Center") == "Node"
        attribute_item = attribute.find("DataItem")
        assert attribute_item.get("Dimensions") == f"{NM_ATOMS}"
        assert f"traj_{index:05d}/lop_sf_fcc" in attribute_item.text


def test_export_uses_absolute_hdf5_references(
    lop_hdf5_path: Path, tmp_path: Path
) -> None:
    output = LopSfFccXdmfExporter(lop_hdf5_path).export(tmp_path / "s.xdmf")
    text = output.read_text()
    assert lop_hdf5_path.resolve().as_posix() in text


def test_export_rejects_a_missing_source(tmp_path: Path) -> None:
    with pytest.raises(PlotterConfigurationError):
        LopSfFccXdmfExporter(tmp_path / "does_not_exist.hdf5")


def test_export_rejects_a_non_hdf5_source(tmp_path: Path) -> None:
    not_hdf5 = tmp_path / "not_hdf5.h5"
    not_hdf5.write_text("this is not HDF5")
    with pytest.raises(PlotterConfigurationError):
        LopSfFccXdmfExporter(not_hdf5)


def test_export_rejects_a_source_without_trajectories(tmp_path: Path) -> None:
    import h5py

    empty = tmp_path / "empty.hdf5"
    with h5py.File(empty, "w") as handle:
        handle.attrs["time_step"] = 0.001
    with pytest.raises(PlotterConfigurationError):
        LopSfFccXdmfExporter(empty).export(tmp_path / "s.xdmf")


def test_export_rejects_a_trajectory_group_with_multiple_frames(
    tmp_path: Path,
) -> None:
    import h5py
    import numpy as np

    source = tmp_path / "multiframe.hdf5"
    with h5py.File(source, "w") as handle:
        handle.attrs["time_step"] = 0.001
        group = handle.create_group("trajectories/traj_00000")
        group.create_dataset("positions", data=np.zeros((2, NM_ATOMS, 3)))
        group.create_dataset("lop_sf_fcc", data=np.zeros((2, NM_ATOMS)))
        group.create_dataset("step_number", data=np.array([0, 1]))
    with pytest.raises(PlotterConfigurationError):
        LopSfFccXdmfExporter(source).export(tmp_path / "s.xdmf")
