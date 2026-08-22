"""Field-aware plotting for TriangleModelGrid.

Free functions taking ``grid`` first, drawing through matplotlib's
object-oriented API and returning the mappable artist. Each ``values``/``u``/``v``
argument accepts either a field-name string, looked up on the matching element
group, or a raw array.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon


def plot_node(grid, values, ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs):
    """Plot a node field as a smooth, full-domain color field.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_node
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> _ = grid.add_field("z", grid.x_of_node, at="node")
    >>> artist = plot_node(grid, "z")
    """
    ax = _resolve_ax(ax)
    values = _resolve_field(grid.at_node, values, grid.number_of_nodes, "node")
    kwargs.setdefault("shading", "gouraud")

    artist = ax.tripcolor(
        grid.x_of_node, grid.y_of_node, grid.nodes_at_patch, values, cmap=cmap, **kwargs
    )
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_link(grid, values, ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs):
    """Plot a link field as line segments colored by value.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_link
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> values = np.arange(grid.number_of_links, dtype=float)
    >>> artist = plot_link(grid, values)
    """
    ax = _resolve_ax(ax)
    values = _resolve_field(grid.at_link, values, grid.number_of_links, "link")

    artist = _plot_segments(ax, grid.xy_of_node[grid.nodes_at_link], values, cmap, **kwargs)
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_patch(grid, values, ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs):
    """Plot a patch field as one flat color per triangle.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_patch
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> values = np.arange(grid.number_of_patches, dtype=float)
    >>> artist = plot_patch(grid, values)
    """
    ax = _resolve_ax(ax)
    values = _resolve_field(grid.at_patch, values, grid.number_of_patches, "patch")

    artist = ax.tripcolor(
        grid.x_of_node, grid.y_of_node, grid.nodes_at_patch, facecolors=values, cmap=cmap, **kwargs
    )
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_corner(grid, values, ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs):
    """Plot a corner field as points colored by value.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_corner
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> values = np.arange(grid.number_of_corners, dtype=float)
    >>> artist = plot_corner(grid, values)
    """
    ax = _resolve_ax(ax)
    values = _resolve_field(grid.at_corner, values, grid.number_of_corners, "corner")

    artist = ax.scatter(grid.x_of_corner, grid.y_of_corner, c=values, cmap=cmap, **kwargs)
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_face(grid, values, ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs):
    """Plot a face field as line segments colored by value.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_face
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> values = np.arange(grid.number_of_faces, dtype=float)
    >>> artist = plot_face(grid, values)
    """
    ax = _resolve_ax(ax)
    values = _resolve_field(grid.at_face, values, grid.number_of_faces, "face")

    artist = _plot_segments(ax, grid.xy_of_corner[grid.corners_at_face], values, cmap, **kwargs)
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_cell(grid, values, ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs):
    """Plot a cell field as flat-colored Voronoi polygons.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_cell
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> values = np.arange(grid.number_of_cells, dtype=float)
    >>> artist = plot_cell(grid, values)
    """
    ax = _resolve_ax(ax)
    values = _resolve_field(grid.at_cell, values, grid.number_of_cells, "cell")

    polygons = [Polygon(_cell_polygon(grid, cell)) for cell in range(grid.number_of_cells)]
    artist = PatchCollection(polygons, cmap=cmap, **kwargs)
    artist.set_array(values)
    ax.add_collection(artist)

    # add_collection does not touch the data limits, so nothing is visible
    # until we autoscale explicitly.
    ax.autoscale_view()
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_vector(
    grid, u, v, at="node", ax=None, cmap=None, colorbar=True, colorbar_label=None, **kwargs
):
    """Plot component vectors as arrows colored by magnitude.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab_triangle import TriangleModelGrid, plot_vector
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> u = np.ones(grid.number_of_nodes)
    >>> artist = plot_vector(grid, u, u, at="node")
    """
    ax = _resolve_ax(ax)
    x, y, group, count = _vector_at(grid, at)
    u = _resolve_field(group, u, count, at)
    v = _resolve_field(group, v, count, at)

    artist = ax.quiver(x, y, u, v, np.hypot(u, v), cmap=cmap, **kwargs)
    _finish(ax, artist, colorbar, colorbar_label)
    return artist


def plot_mesh(grid, ax=None, **kwargs):
    """Plot the mesh skeleton as the links between nodes.

    Examples
    --------
    >>> from landlab_triangle import TriangleModelGrid, plot_mesh
    >>> grid = TriangleModelGrid(
    ...     [0.0, 10.0, 10.0, 0.0], [-1.0, -1.0, 11.0, 11.0], triangle_options="pqa5Devjz"
    ... )
    >>> artist = plot_mesh(grid, color="0.5")
    """
    ax = _resolve_ax(ax)
    ends = grid.xy_of_node[grid.nodes_at_link]

    artist = LineCollection(ends, **kwargs)
    ax.add_collection(artist)
    ax.autoscale_view()
    ax.set_aspect("equal")
    return artist


def _plot_segments(ax, ends, values, cmap, **kwargs):
    """Add a value-colored LineCollection and return it as a scalar mappable."""
    artist = LineCollection(ends, cmap=cmap, **kwargs)
    artist.set_array(values)
    ax.add_collection(artist)
    ax.autoscale_view()
    return artist


def _resolve_ax(ax):
    return ax if ax is not None else plt.gca()


def _resolve_field(group, values, expected, at):
    if isinstance(values, str):
        values = group[values]
    values = np.asarray(values)

    if values.shape[0] != expected:
        raise ValueError(f"expected {expected} values at {at}, got {values.shape[0]}")

    return values


def _vector_at(grid, at):
    if at == "node":
        return grid.x_of_node, grid.y_of_node, grid.at_node, grid.number_of_nodes
    if at == "cell":
        return grid.xy_of_cell[:, 0], grid.xy_of_cell[:, 1], grid.at_cell, grid.number_of_cells
    raise ValueError(f"'at' must be 'node' or 'cell', got {at!r}")


def _cell_polygon(grid, cell):
    """Corner coordinates of one Voronoi cell, wound counter-clockwise."""
    corners = grid.corners_at_cell[cell]
    corners = corners[corners != -1]
    xy = np.c_[grid.x_of_corner[corners], grid.y_of_corner[corners]]

    # corners_at_cell is not stored in polygon order, so a raw fill would
    # self-intersect; sort by angle about the centroid to wind the ring.
    angle = np.arctan2(xy[:, 1] - xy[:, 1].mean(), xy[:, 0] - xy[:, 0].mean())
    return xy[np.argsort(angle)]


def _finish(ax, artist, colorbar, colorbar_label):
    ax.set_aspect("equal")
    if colorbar:
        bar = ax.figure.colorbar(artist, ax=ax)
        if colorbar_label is not None:
            bar.set_label(colorbar_label)
