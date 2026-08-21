"""Behavioral smoke tests for the plotting functions, on the Agg backend."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.cm import ScalarMappable
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.quiver import Quiver

from landlab_triangle import (
    TriangleModelGrid,
    plot_cell,
    plot_corner,
    plot_face,
    plot_link,
    plot_mesh,
    plot_node,
    plot_patch,
    plot_vector,
)
from landlab_triangle.mesh import TriangleMesh

if not TriangleMesh.validate_triangle():
    pytestmark = pytest.mark.skip(reason="triangle is not installed")

SCALAR_PLOTTERS = [
    ("node", plot_node),
    ("link", plot_link),
    ("patch", plot_patch),
    ("corner", plot_corner),
    ("face", plot_face),
    ("cell", plot_cell),
]


@pytest.fixture
def grid():
    return TriangleModelGrid(
        ([-1.0, -1.0, 11.0, 11.0], [0.0, 10.0, 10.0, 0.0]), triangle_opts="pqa5Devjz"
    )


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _count(grid, at):
    plural = "patches" if at == "patch" else f"{at}s"
    return getattr(grid, f"number_of_{plural}")


def _values(grid, at):
    return np.arange(_count(grid, at), dtype=float)


@pytest.mark.parametrize("at, func", SCALAR_PLOTTERS)
def test_returns_mappable_landed_on_axes(grid, at, func):
    ax = plt.gca()
    artist = func(grid, _values(grid, at))

    assert isinstance(artist, ScalarMappable)
    assert artist.axes is ax
    assert ax.has_data()


@pytest.mark.parametrize("at, func", SCALAR_PLOTTERS)
def test_field_name_matches_raw_array(grid, at, func):
    values = _values(grid, at)
    getattr(grid, f"at_{at}")["f"] = values

    from_name = func(grid, "f")
    plt.close("all")
    from_array = func(grid, values)

    assert np.allclose(from_name.get_array(), from_array.get_array())


@pytest.mark.parametrize("at, func", SCALAR_PLOTTERS)
def test_colorbar_present_only_when_requested(grid, at, func):
    ax = plt.gca()
    func(grid, _values(grid, at), colorbar=True)
    assert len(ax.figure.axes) == 2

    plt.close("all")
    ax = plt.gca()
    func(grid, _values(grid, at), colorbar=False)
    assert len(ax.figure.axes) == 1


@pytest.mark.parametrize("at, func", SCALAR_PLOTTERS)
def test_draws_on_passed_axes(grid, at, func):
    _, (left, right) = plt.subplots(1, 2)
    func(grid, _values(grid, at), ax=right, colorbar=False)

    assert right.has_data()
    assert not left.has_data()


@pytest.mark.parametrize("at, func", SCALAR_PLOTTERS)
def test_cmap_reaches_artist(grid, at, func):
    artist = func(grid, _values(grid, at), cmap="plasma")
    assert artist.get_cmap().name == "plasma"


@pytest.mark.parametrize("at, func", SCALAR_PLOTTERS)
def test_wrong_length_raises(grid, at, func):
    with pytest.raises(ValueError):
        func(grid, np.zeros(3))


def test_vector_returns_quiver_on_axes(grid):
    ax = plt.gca()
    u = np.ones(grid.number_of_nodes)
    artist = plot_vector(grid, u, u)

    assert isinstance(artist, Quiver)
    assert ax.has_data()


def test_vector_at_cell(grid):
    u = np.ones(grid.number_of_cells)
    artist = plot_vector(grid, u, u, at="cell")
    assert isinstance(artist, Quiver)


def test_vector_accepts_field_names(grid):
    grid.at_node["u"] = np.ones(grid.number_of_nodes)
    grid.at_node["v"] = 2.0 * np.ones(grid.number_of_nodes)
    artist = plot_vector(grid, "u", "v")
    assert isinstance(artist, Quiver)


def test_vector_rejects_bad_location(grid):
    u = np.ones(grid.number_of_nodes)
    with pytest.raises(ValueError):
        plot_vector(grid, u, u, at="patch")


def test_vector_wrong_length_raises(grid):
    with pytest.raises(ValueError):
        plot_vector(grid, np.zeros(3), np.zeros(3))


def test_mesh_returns_linecollection_on_axes(grid):
    ax = plt.gca()
    artist = plot_mesh(grid)

    assert isinstance(artist, LineCollection)
    assert artist.axes is ax
    assert ax.has_data()


def test_mesh_kwargs_reach_artist(grid):
    artist = plot_mesh(grid, color="red")
    assert np.allclose(artist.get_color()[0], to_rgba("red"))
