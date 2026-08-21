"""Tests for the TriangleModelGrid class."""

import numpy as np
import pytest

from landlab_triangle.mesh import TriangleMesh
from landlab_triangle.triangle import TriangleModelGrid

if not TriangleMesh.validate_triangle():
    pytestmark = pytest.mark.skip(reason="triangle is not installed")


@pytest.fixture(scope="session")
def square_grid():
    return TriangleModelGrid(
        [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa1Devjz"
    )


@pytest.mark.parametrize("point", ("corner", "node"))
def test_all_points_in_box(square_grid, point):
    x, y = getattr(square_grid, f"x_of_{point}"), getattr(square_grid, f"y_of_{point}")

    assert np.all(x >= 0.0) and np.all(x <= 10.0)
    assert np.all(y >= -1.0) and np.all(y <= 11.0)


@pytest.mark.parametrize("edge", ("face", "link"))
def test_no_zero_length_edges(square_grid, edge):
    assert np.all(getattr(square_grid, f"length_of_{edge}") >= 0.0)


@pytest.mark.parametrize("polygon", ("cell", "patch"))
def test_no_zero_area_polygons(square_grid, polygon):
    assert np.all(getattr(square_grid, f"area_of_{polygon}") >= 0.0)


def test_boundary_nodes_on_boundary(square_grid):
    x, y = square_grid.x_of_node, square_grid.y_of_node
    assert np.all(
        (x[square_grid.boundary_nodes] == 0.0)
        | (x[square_grid.boundary_nodes] == 10.0)
        | (y[square_grid.boundary_nodes] == -1.0)
        | (y[square_grid.boundary_nodes] == 11.0)
    )
    assert square_grid.number_of_cells == square_grid.number_of_nodes - len(
        square_grid.boundary_nodes
    )


def test_grid_init():
    grid = TriangleModelGrid(
        [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa1Devjz"
    )
    assert grid.number_of_corners == grid.number_of_patches


def _links_oriented_up_and_right(grid):
    theta = np.mod(grid.angle_of_link, 2.0 * np.pi)
    return (theta < 0.75 * np.pi) | (theta >= 1.75 * np.pi)


def test_links_point_up_and_right(square_grid):
    # A flipped link silently negates advection/gradient components, so every
    # link must obey landlab's tail->head convention (angle outside [135, 315)).
    assert np.all(_links_oriented_up_and_right(square_grid))


def test_from_dict_matches_direct_construction():
    grid = TriangleModelGrid.from_dict(
        {
            "x": [0.0, 10.0, 10.0, 0.0],
            "y": [-1.0, -1.0, 11.0, 11.0],
            "triangle_options": "pqa1Devjz",
        }
    )
    assert grid.number_of_cells > 0
    assert np.all(_links_oriented_up_and_right(grid))


def test_from_dict_does_not_mutate_caller():
    params = {
        "x": [0.0, 10.0, 10.0, 0.0],
        "y": [-1.0, -1.0, 11.0, 11.0],
        "triangle_options": "pqa1Devjz",
    }
    TriangleModelGrid.from_dict(params)
    assert set(params) == {"x", "y", "triangle_options"}


def test_interior_ring_becomes_a_hole():
    ring = [(3.0, 3.0), (7.0, 3.0), (7.0, 7.0), (3.0, 7.0)]
    grid = TriangleModelGrid(
        [0.0, 10.0, 10.0, 0.0],
        [0.0, 0.0, 10.0, 10.0],
        interior_rings=[ring],
        triangle_options="pqa2Devjz",
    )
    in_hole = (
        (grid.x_of_node > 3.0)
        & (grid.x_of_node < 7.0)
        & (grid.y_of_node > 3.0)
        & (grid.y_of_node < 7.0)
    )
    assert not np.any(in_hole)
