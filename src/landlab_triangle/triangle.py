"""Python implementation of TriangleModelGrid, a class used to create and
manage unstructured, irregular grids for 2D numerical models.
"""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
from landlab.grid.base import ModelGrid

from landlab_triangle import ugrid
from landlab_triangle.graph import DualTriangleGraph


class TriangleModelGrid(DualTriangleGraph, ModelGrid):
    """This inherited class implements an unstructured grid from dual
    Delaunay and Voronoi graphs. By convention, nodes, links, and patches
    compose a Delaunay triangulation, while corners, faces, and cells
    compose the corresponding Voronoi tesselation. Uses the Triangle
    software package to build the mesh.

    Create an unstructured grid from points whose coordinates are given
    by the arrays *x*, *y*.

    Returns
    -------
    TriangleModelGrid
        A newly-created grid.

    See also
    --------
    TriangleGraph.from_shapefile
        Constructs the grid from a shapefile, geojson, geopackage, etc.

    Examples
    --------
    """

    def __init__(
        self,
        exterior_y_and_x: tuple[np.ndarray, np.ndarray],
        holes=None,
        triangle_opts="pqDevjz",
        timeout=11,
        reorient_links=False,
        xy_of_reference=(0.0, 0.0),
        xy_axis_name=("x", "y"),
        xy_axis_units="-",
        sort=False,
    ):
        """Create a TriangleModelGrid from a set of points.

        Create an unstructured grid from points whose coordinates are given
        by the arrays *x*, *y*.

        Parameters
        ----------
        x : array_like
            x-coordinate of points
        y : array_like
            y-coordinate of points
        holes : array_like
            (N, 2) shaped array with coordinates of any holes in the domain
        triangle_opts : str
            command-line options for the Triangle meshing software
        timeout : float
            how many seconds to allow Triangle to run before terminating
        reorient_links (optional) : bool
            whether to point all links to the upper-right quadrant
        xy_of_reference : tuple, optional
            Coordinate value in projected space of (0., 0.)
            Default is (0., 0.)

        Returns
        -------
        TriangleModelGrid
            A newly-created grid.

        Examples
        --------
        """
        DualTriangleGraph.__init__(
            self,
            exterior_y_and_x,
            holes=holes,
            triangle_opts=triangle_opts,
            timeout=timeout,
            sort=sort,
        )
        ModelGrid.__init__(
            self,
            xy_axis_name=xy_axis_name,
            xy_axis_units=xy_axis_units,
            xy_of_reference=xy_of_reference,
        )

        self._node_status = np.full(self.number_of_nodes, self.BC_NODE_IS_CORE, dtype=np.uint8)
        self._node_status[self.perimeter_nodes] = self.BC_NODE_IS_FIXED_VALUE

    @classmethod
    def from_dict(cls, kwds):
        """Initialize a new TriangleModelGrid from a dict with "x" and "y" keys."""
        args = (kwds.pop("x"), kwds.pop("y"))
        return cls(*args, **kwds)

    def plot_nodes_and_links(
        self,
        nodes_args: dict = None,
        links_args: dict = None,
        subplots_args: dict = None,
    ):
        """Produce a plot of nodes and links."""
        if nodes_args is None:
            nodes_args = {}
        if links_args is None:
            links_args = {}
        if subplots_args is None:
            subplots_args = {}

        fig, ax = plt.subplots(**subplots_args)

        for link in np.arange(self.number_of_links):
            head, tail = self.nodes_at_link[link]
            ax.plot(
                [self.x_of_node[head], self.x_of_node[tail]],
                [self.y_of_node[head], self.y_of_node[tail]],
                **links_args,
            )

        ax.scatter(self.x_of_node, self.y_of_node, **nodes_args)

        return fig

    def save(self, path, clobber=False):
        """Save the grid and all its fields to a CF-UGRID netCDF file.

        Writes the primal Delaunay and dual Voronoi meshes as two
        ``mesh_topology`` variables in one file, readable again by :meth:`load`
        or by ParaView/QGIS/xarray/uxarray. A ``.nc`` suffix is added if
        missing. Returns the path written.

        Parameters
        ----------
        path : str
            Path to output file.
        clobber : bool, optional
            Allow overwriting an existing file (default False).
        """
        path = pathlib.Path(path)

        if path.suffix != ".nc":
            path = path.with_suffix(path.suffix + ".nc")

        if path.exists() and not clobber:
            raise ValueError(
                f"File exists: {str(path)!r}. "
                "Either remove this file and try again or set the "
                "'clobber' keyword to True"
            )

        return ugrid.write_ugrid(self, path)

    @classmethod
    def load(cls, path):
        """Reconstruct a grid from a ``.nc`` file written by :meth:`save`.

        Rebuilds from the stored topology alone; the Triangle binary is never
        re-run. Topology passes through the same construction tail as a fresh
        grid, then fields and node status are restored.
        """
        data = ugrid.read_ugrid(path)

        grid = cls.__new__(cls)
        grid._delaunay = data["delaunay"]
        grid._voronoi = data["voronoi"]

        DualTriangleGraph._build_from_dicts(grid, sort=False)

        ModelGrid.__init__(
            grid,
            xy_axis_name=("x", "y"),
            xy_axis_units=data["units"],
        )

        grid._node_status = np.asarray(data["node_status"], dtype=np.uint8)

        for location, field_group in data["fields"].items():
            for name, values in field_group.items():
                grid.add_field(name, values, at=location, clobber=True)

        return grid
