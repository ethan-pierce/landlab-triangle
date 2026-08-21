"""Tests for UGRID netCDF export/import of TriangleModelGrid."""

import numpy as np
import pytest
import xarray as xr

from landlab_triangle import ugrid
from landlab_triangle.mesh import TriangleMesh
from landlab_triangle.triangle import TriangleModelGrid

if not TriangleMesh.validate_triangle():
    pytestmark = pytest.mark.skip(reason="triangle is not installed")


@pytest.fixture(scope="module")
def square_grid():
    return TriangleModelGrid(
        [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa1Devjz"
    )


def _add_mixed_fields(grid):
    """A field at every location, mixed dtypes, with ``elevation`` at both node
    and cell to exercise the same-name-different-location case."""
    grid.add_field("elevation", np.arange(grid.number_of_nodes, dtype=float), at="node")
    grid.add_field("is_active", (np.arange(grid.number_of_links) % 2).astype(bool), at="link")
    grid.add_field("patch_id", np.arange(grid.number_of_patches, dtype=np.int32), at="patch")
    grid.add_field("corner_x", grid.x_of_corner.copy(), at="corner")
    grid.add_field("flux", np.linspace(0.0, 1.0, grid.number_of_faces), at="face")
    grid.add_field("elevation", np.arange(grid.number_of_cells, dtype=float) * 2.0, at="cell")
    return grid


def test_save_returns_nc_suffix(square_grid, tmp_path):
    out = square_grid.save(str(tmp_path / "mesh"))
    assert out.endswith(".nc")


def test_save_refuses_to_clobber(square_grid, tmp_path):
    path = tmp_path / "mesh.nc"
    square_grid.save(str(path))
    with pytest.raises(ValueError, match="File exists"):
        square_grid.save(str(path))
    square_grid.save(str(path), clobber=True)


def test_roundtrip_topology(square_grid, tmp_path):
    path = str(tmp_path / "mesh.nc")
    square_grid.save(path)
    loaded = TriangleModelGrid.load(path)

    for attr in (
        "x_of_node",
        "y_of_node",
        "nodes_at_link",
        "nodes_at_patch",
        "x_of_corner",
        "y_of_corner",
        "corners_at_face",
        "corners_at_cell",
        "node_at_cell",
        "nodes_at_face",
    ):
        np.testing.assert_array_equal(
            getattr(square_grid, attr), getattr(loaded, attr), err_msg=attr
        )


def test_roundtrip_counts(square_grid, tmp_path):
    path = str(tmp_path / "mesh.nc")
    loaded = TriangleModelGrid.load(square_grid.save(path))

    for count in (
        "number_of_nodes",
        "number_of_links",
        "number_of_patches",
        "number_of_corners",
        "number_of_faces",
        "number_of_cells",
    ):
        assert getattr(square_grid, count) == getattr(loaded, count), count


def test_roundtrip_node_status(square_grid, tmp_path):
    path = str(tmp_path / "mesh.nc")
    loaded = TriangleModelGrid.load(square_grid.save(path))
    np.testing.assert_array_equal(square_grid._node_status, loaded._node_status)
    assert loaded._node_status.dtype == np.uint8


def test_roundtrip_edited_node_status(square_grid, tmp_path):
    """A post-hoc boundary-condition edit survives the round-trip."""
    grid = TriangleModelGrid.load(square_grid.save(str(tmp_path / "seed.nc")))
    grid.status_at_node[grid.perimeter_nodes[0]] = grid.BC_NODE_IS_CLOSED
    edited = grid._node_status.copy()

    path = str(tmp_path / "edited.nc")
    loaded = TriangleModelGrid.load(grid.save(path))
    np.testing.assert_array_equal(loaded._node_status, edited)


def test_roundtrip_closed_interior_node_keeps_cells(square_grid, tmp_path):
    """Closing an interior node must not drop or renumber cells on reload.

    The Triangle boundary marker (which nodes get cells) is topology, not the
    mutable node status; deriving it from status would lose an interior node's
    cell here.
    """
    grid = TriangleModelGrid.load(square_grid.save(str(tmp_path / "seed.nc")))
    grid.add_field("cell_id", np.arange(grid.number_of_cells, dtype=float), at="cell")
    interior = int(np.flatnonzero(grid._node_status == grid.BC_NODE_IS_CORE)[0])
    grid.status_at_node[interior] = grid.BC_NODE_IS_CLOSED

    path = str(tmp_path / "closed.nc")
    loaded = TriangleModelGrid.load(grid.save(path))
    assert loaded.number_of_cells == grid.number_of_cells
    np.testing.assert_array_equal(loaded.at_cell["cell_id"], grid.at_cell["cell_id"])


def test_roundtrip_units(tmp_path):
    """Axis units survive the round-trip."""
    grid = TriangleModelGrid(
        [0.0, 10.0, 10.0, 0.0],
        [-1.0, -1.0, 11.0, 11.0],
        triangle_options="pqa1Devjz",
        xy_axis_units=("m", "m"),
    )
    loaded = TriangleModelGrid.load(grid.save(str(tmp_path / "mesh.nc")))
    assert tuple(loaded.axis_units) == ("m", "m")


def test_roundtrip_preserves_link_orientation(square_grid, tmp_path):
    loaded = TriangleModelGrid.load(square_grid.save(str(tmp_path / "mesh.nc")))
    theta = np.mod(loaded.angle_of_link, 2.0 * np.pi)
    assert np.all((theta < 0.75 * np.pi) | (theta >= 1.75 * np.pi))


def test_roundtrip_preserves_axis_metadata(tmp_path):
    grid = TriangleModelGrid(
        [0.0, 10.0, 10.0, 0.0],
        [-1.0, -1.0, 11.0, 11.0],
        triangle_options="pqa1Devjz",
        xy_axis_name=("easting", "northing"),
        xy_of_reference=(500000.0, 4000000.0),
    )
    loaded = TriangleModelGrid.load(grid.save(str(tmp_path / "mesh.nc")))
    assert tuple(loaded.axis_name) == ("easting", "northing")
    assert tuple(loaded.xy_of_reference) == (500000.0, 4000000.0)


def test_roundtrip_preserves_field_units(square_grid, tmp_path):
    grid = TriangleModelGrid.load(square_grid.save(str(tmp_path / "seed.nc")))
    grid.add_field(
        "elevation", np.arange(grid.number_of_nodes, dtype=float), at="node", units="meters"
    )
    loaded = TriangleModelGrid.load(grid.save(str(tmp_path / "units.nc")))
    assert loaded.at_node.dataset["elevation"].attrs.get("units") == "meters"


def test_roundtrip_fields(square_grid, tmp_path):
    grid = _add_mixed_fields(TriangleModelGrid.load(square_grid.save(str(tmp_path / "seed.nc"))))
    path = str(tmp_path / "fields.nc")
    loaded = TriangleModelGrid.load(grid.save(path))

    for location in ("node", "link", "patch", "corner", "face", "cell"):
        original = getattr(grid, f"at_{location}")
        restored = getattr(loaded, f"at_{location}")
        assert set(original.keys()) == set(restored.keys()), location
        for name in original.keys():
            np.testing.assert_array_equal(
                original[name], restored[name], err_msg=f"{name}@{location}"
            )
            assert original[name].dtype == restored[name].dtype, f"{name}@{location}"


def test_same_field_name_at_two_locations(square_grid, tmp_path):
    grid = _add_mixed_fields(TriangleModelGrid.load(square_grid.save(str(tmp_path / "seed.nc"))))
    path = str(tmp_path / "dup.nc")
    loaded = TriangleModelGrid.load(grid.save(path))
    # 'elevation' exists at both node and cell and must stay distinct.
    assert not np.array_equal(
        loaded.at_node["elevation"][: loaded.number_of_cells],
        loaded.at_cell["elevation"],
    )
    np.testing.assert_array_equal(loaded.at_cell["elevation"], grid.at_cell["elevation"])


def test_fresh_vs_loaded_structural_equivalence(square_grid, tmp_path):
    """The recompute-on-load path must reproduce a freshly-built grid."""
    path = str(tmp_path / "mesh.nc")
    loaded = TriangleModelGrid.load(square_grid.save(path))

    for attr in (
        "x_of_node",
        "y_of_node",
        "nodes_at_link",
        "links_at_patch",
        "nodes_at_patch",
        "x_of_corner",
        "y_of_corner",
        "corners_at_face",
        "faces_at_cell",
        "corners_at_cell",
        "node_at_cell",
        "cell_at_node",
        "nodes_at_face",
        "length_of_link",
        "length_of_face",
        "area_of_patch",
        "area_of_cell",
    ):
        np.testing.assert_allclose(getattr(square_grid, attr), getattr(loaded, attr), err_msg=attr)


def test_ugrid_structure(square_grid, tmp_path):
    path = str(tmp_path / "mesh.nc")
    square_grid.save(path)

    with xr.open_dataset(path) as ds:
        for mesh in ("mesh2d_delaunay", "mesh2d_voronoi"):
            assert ds[mesh].attrs["cf_role"] == "mesh_topology"
            assert ds[mesh].attrs["topology_dimension"] == 2
            assert "node_coordinates" in ds[mesh].attrs
            assert "edge_node_connectivity" in ds[mesh].attrs
            assert "face_node_connectivity" in ds[mesh].attrs

        for conn in (
            "mesh2d_delaunay_edge_nodes",
            "mesh2d_delaunay_face_nodes",
            "mesh2d_voronoi_edge_nodes",
            "mesh2d_voronoi_face_nodes",
        ):
            assert ds[conn].attrs["start_index"] == 0
            assert ds[conn].encoding.get("_FillValue") == -1

        for coord in (
            "mesh2d_delaunay_node_x",
            "mesh2d_voronoi_node_x",
        ):
            assert ds[coord].attrs["standard_name"] == "projection_x_coordinate"
            assert "units" in ds[coord].attrs

        assert ds.attrs["landlab_triangle_version"]


def test_field_cf_attrs(square_grid, tmp_path):
    grid = _add_mixed_fields(TriangleModelGrid.load(square_grid.save(str(tmp_path / "seed.nc"))))
    path = str(tmp_path / "fields.nc")
    grid.save(path)

    expected = {
        "elevation_at_node": ("mesh2d_delaunay", "node"),
        "is_active_at_link": ("mesh2d_delaunay", "edge"),
        "patch_id_at_patch": ("mesh2d_delaunay", "face"),
        "corner_x_at_corner": ("mesh2d_voronoi", "node"),
        "flux_at_face": ("mesh2d_voronoi", "edge"),
        "elevation_at_cell": ("mesh2d_voronoi", "face"),
    }
    with xr.open_dataset(path) as ds:
        for var, (mesh, location) in expected.items():
            assert ds[var].attrs["mesh"] == mesh, var
            assert ds[var].attrs["location"] == location, var


def test_read_rejects_non_landlab_file(tmp_path):
    path = str(tmp_path / "foreign.nc")
    xr.Dataset({"foo": ("x", np.arange(3))}).to_netcdf(path)
    with pytest.raises(ValueError, match="not a landlab-triangle UGRID file"):
        ugrid.read_ugrid(path)


try:
    import uxarray
except ImportError:  # uxarray is a dev/test-only dependency
    uxarray = None

requires_uxarray = pytest.mark.skipif(uxarray is None, reason="uxarray is a dev-only dependency")


@requires_uxarray
def test_uxarray_reads_primal_mesh(square_grid, tmp_path):
    """uxarray auto-selects the first mesh_topology (the primal Delaunay);
    use_dual only applies to MPAS files, not generic UGRID."""
    path = str(tmp_path / "mesh.nc")
    square_grid.save(path)

    uxgrid = uxarray.open_grid(path)

    assert uxgrid.n_node == square_grid.number_of_nodes
    assert uxgrid.n_face == square_grid.number_of_patches


@requires_uxarray
def test_uxarray_reads_dual_mesh(square_grid, tmp_path):
    """uxarray reads the Voronoi mesh when handed its subset of variables."""
    path = str(tmp_path / "mesh.nc")
    square_grid.save(path)

    with xr.open_dataset(path) as ds:
        voronoi = ds[
            [
                "mesh2d_voronoi",
                "mesh2d_voronoi_node_x",
                "mesh2d_voronoi_node_y",
                "mesh2d_voronoi_edge_nodes",
                "mesh2d_voronoi_face_nodes",
            ]
        ]

    uxgrid = uxarray.open_grid(voronoi)

    assert uxgrid.n_node == square_grid.number_of_corners
    assert uxgrid.n_face == square_grid.number_of_cells
