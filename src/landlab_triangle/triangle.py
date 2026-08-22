"""Python implementation of TriangleModelGrid, a class used to create and
manage unstructured, irregular grids for 2D numerical models.
"""

import pathlib

import numpy as np
from landlab.grid.base import ModelGrid

from landlab_triangle import ugrid
from landlab_triangle.graph import DualTriangleGraph
from landlab_triangle.mesh import TriangleMesh


class TriangleModelGrid(DualTriangleGraph, ModelGrid):
    """An unstructured Landlab grid built from dual Delaunay and Voronoi graphs.

    Nodes, links, and patches compose a Delaunay triangulation; corners, faces,
    and cells compose the corresponding Voronoi tesselation. Jonathan Shewchuk's
    Triangle package meshes the interior of a boundary polygon.

    See also
    --------
    TriangleModelGrid.from_vector_file
        Build the grid from a GeoJSON, GeoPackage, shapefile, etc.
    """

    def __init__(
        self,
        x_of_boundary,
        y_of_boundary,
        interior_rings=None,
        *,
        triangle_options=TriangleMesh.default_opts,
        timeout=10,
        xy_of_reference=(0.0, 0.0),
        xy_axis_name=("x", "y"),
        xy_axis_units="-",
    ):
        """Mesh the interior of a boundary polygon.

        Parameters
        ----------
        x_of_boundary, y_of_boundary : array_like
            Coordinates of the exterior boundary vertices, in order. These are
            the outline; Triangle generates the interior nodes.
        interior_rings : sequence of rings, optional
            Holes, each an (N, 2) sequence of (x, y) vertices, as Shapely's
            ``holes`` argument.
        triangle_options : str, optional
            Command-line switches for Triangle (default ``"pqDevjz"``).
        timeout : float, optional
            Seconds to allow Triangle to run before raising ``TriangleError``.
        xy_of_reference : tuple, optional
            Coordinate in projected space of ``(0.0, 0.0)``.
        xy_axis_name : tuple of str, optional
        xy_axis_units : str, optional

        Raises
        ------
        TriangleError
            If Triangle fails to mesh the domain or exceeds ``timeout`` seconds.
        """
        DualTriangleGraph.__init__(
            self,
            x_of_boundary,
            y_of_boundary,
            interior_rings=interior_rings,
            triangle_options=triangle_options,
            timeout=timeout,
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
    def from_dict(cls, params):
        """Build a grid from a dict with ``"x"``/``"y"`` boundary coordinates.

        Remaining keys pass through as keyword arguments; the caller's dict is
        left unmodified.
        """
        params = dict(params)
        x_of_boundary = params.pop("x")
        y_of_boundary = params.pop("y")
        return cls(x_of_boundary, y_of_boundary, **params)

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

        DualTriangleGraph._build_from_dicts(grid)

        ModelGrid.__init__(
            grid,
            xy_axis_name=data["axis_name"],
            xy_axis_units=data["units"],
            xy_of_reference=data["xy_of_reference"],
        )

        grid._node_status = np.asarray(data["node_status"], dtype=np.uint8)

        for location, field_group in data["fields"].items():
            for name, (values, units) in field_group.items():
                grid.add_field(name, values, at=location, units=units, clobber=True)

        return grid
