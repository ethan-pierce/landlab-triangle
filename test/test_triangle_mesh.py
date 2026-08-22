"""Tests for the TriangleMesh object."""

import subprocess

import numpy as np
import pytest
import shapely
from numpy.testing import assert_array_equal

from landlab_triangle.mesh import TriangleError, TriangleMesh

try:
    TriangleMesh.validate_triangle()
except FileNotFoundError:
    pytestmark = pytest.mark.skip(reason="triangle is not installed")


xy_points = np.array(
    [
        [0.0, 0.0],
        [1.0, 0.0],
        [2.0, 0.0],
        [0.5, 1.0],
        [1.5, 1.0],
        [2.5, 1.0],
        [0.0, 2.0],
        [1.0, 2.0],
        [2.0, 2.0],
        [0.0, 3.0],
        [1.0, 3.0],
        [2.0, 3.0],
        [0.0, 0.0],
    ]
)


def test_init_from_points():
    """Test initialization from list of points."""
    mesh = TriangleMesh.from_points(xy_points, opts="pqDevjz")

    # The final point duplicates the first, so it is dropped from _vertices.
    assert mesh._vertices.shape == (xy_points.shape[0] - 1, 2)
    assert mesh._segments.shape == (xy_points.shape[0] - 1, 2)
    assert mesh._holes is None
    assert mesh._opts == "pqDevjz"


def test_triangulate_from_points():
    """Test triangulation routine."""
    mesh = TriangleMesh.from_points(xy_points, opts="pqDevjz")
    mesh.triangulate()


def test_init_from_geojson(geojson_concave_polygon):
    """Test initialization from a geojson file."""
    mesh = TriangleMesh.from_vector_file(geojson_concave_polygon, opts="pqDevjz")

    assert_array_equal(
        mesh._vertices,
        [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [5.0, 15.0],
            [0.0, 10.0],
            [2.0, 2.0],
            [8.0, 2.0],
            [8.0, 8.0],
            [2.0, 8.0],
        ],
    )

    assert_array_equal(mesh._holes, [[5.0, 5.0]])

    assert_array_equal(
        mesh._segments,
        [[5, 6], [6, 7], [7, 8], [8, 5], [0, 1], [1, 2], [2, 3], [3, 4], [4, 0]],
    )

    assert mesh._opts == "pqDevjz"


def test_triangulate_from_geojson(geojson_concave_polygon):
    """Test triangulation routine."""
    mesh = TriangleMesh.from_vector_file(geojson_concave_polygon, opts="pqDevjz")
    mesh.triangulate()


def test_segment(geojson_concave_polygon):
    "Test segmentation routine."
    mesh = TriangleMesh.from_vector_file(geojson_concave_polygon, opts="pqDevjz")
    segments = mesh._segment(mesh._poly)

    assert len(mesh._holes) == len(mesh._poly.interiors)
    assert len(segments) == 9

    for hole in mesh._holes:
        point = shapely.Point(hole)

        assert not mesh._poly.contains(point)


def test_no_duplicate_vertices(geojson_concave_polygon):
    """Vertices passed to Triangle must not contain exact duplicates, which
    trip an out-of-bounds read in Triangle's duplicate-vertex handling."""
    for mesh in (
        TriangleMesh.from_points(xy_points, opts="pqDevjz"),
        TriangleMesh.from_vector_file(geojson_concave_polygon, opts="pqDevjz"),
    ):
        unique = np.unique(mesh._vertices, axis=0)
        assert unique.shape[0] == mesh._vertices.shape[0]


def test_geojson_then_points_does_not_crash(geojson_concave_polygon):
    """Reading a geojson loads GDAL, which shifts the process memory layout.
    A duplicate vertex would then crash Triangle; triangulating from points
    afterwards in the same process must still succeed."""
    TriangleMesh.from_vector_file(geojson_concave_polygon, opts="pqDevjz").triangulate()

    mesh = TriangleMesh.from_points(xy_points, opts="pqDevjz")
    mesh.triangulate()

    assert mesh.delaunay is not None
    assert mesh.voronoi is not None


def test_triangulate_surfaces_nonzero_exit(monkeypatch):
    """A nonzero Triangle exit surfaces its own message as a TriangleError."""
    mesh = TriangleMesh.from_points(xy_points, opts="pqDevjz")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, returncode=1, stdout=b"Error:  bad geometry.\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(TriangleError) as excinfo:
        mesh.triangulate()

    message = str(excinfo.value)
    assert "exit code 1" in message
    assert "bad geometry" in message


def test_triangulate_surfaces_timeout(monkeypatch):
    """A Triangle timeout surfaces as a TriangleError naming the timeout."""
    mesh = TriangleMesh.from_points(xy_points, opts="pqDevjz")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="triangle", timeout=mesh._timeout)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(TriangleError, match="did not finish within"):
        mesh.triangulate()
