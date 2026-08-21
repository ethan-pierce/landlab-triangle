"""Read and write TriangleModelGrid grids as CF-UGRID netCDF files.

The durable serialization format, replacing pickle: the primal Delaunay and dual
Voronoi meshes go into one file as two ``mesh_topology`` variables, along with
every field. The primal-dual bridge is recomputed on load rather than stored, so
:func:`read_ugrid` returns only raw topology. The non-UGRID additions are
``landlab_node_status`` (captures boundary edits), ``landlab_node_bc`` (the
Triangle boundary marker, which fixes cell membership), and the
``landlab_triangle_version`` global attribute.
"""

from __future__ import annotations

import importlib.metadata

import numpy as np
import pandas as pd
import xarray as xr

# landlab grid location -> (mesh_topology variable, UGRID location)
_LOCATION_TO_MESH = {
    "node": ("mesh2d_delaunay", "node"),
    "link": ("mesh2d_delaunay", "edge"),
    "patch": ("mesh2d_delaunay", "face"),
    "corner": ("mesh2d_voronoi", "node"),
    "face": ("mesh2d_voronoi", "edge"),
    "cell": ("mesh2d_voronoi", "face"),
}

_LOCATION_TO_DIM = {
    "node": "n_mesh2d_delaunay_node",
    "link": "n_mesh2d_delaunay_edge",
    "patch": "n_mesh2d_delaunay_face",
    "corner": "n_mesh2d_voronoi_node",
    "face": "n_mesh2d_voronoi_edge",
    "cell": "n_mesh2d_voronoi_face",
}

_FILL_VALUE = -1


def _version() -> str:
    """Return the installed landlab-triangle version, or ``"unknown"``."""
    try:
        return importlib.metadata.version("landlab-triangle")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


def write_ugrid(grid, path) -> str:
    """Write *grid* and all its fields to a CF-UGRID netCDF file, returning *path*."""
    delaunay = grid._delaunay
    voronoi = grid._voronoi

    units = getattr(grid, "axis_units", ("-", "-"))
    x_units, y_units = str(units[0]), str(units[1])

    axis_name = getattr(grid, "axis_name", ("x", "y"))
    xy_of_reference = getattr(grid, "xy_of_reference", (0.0, 0.0))

    data_vars = {}

    data_vars["mesh2d_delaunay"] = xr.DataArray(
        np.int32(0),
        attrs={
            "cf_role": "mesh_topology",
            "long_name": "Delaunay triangulation (primal mesh)",
            "topology_dimension": 2,
            "node_coordinates": "mesh2d_delaunay_node_x mesh2d_delaunay_node_y",
            "edge_node_connectivity": "mesh2d_delaunay_edge_nodes",
            "face_node_connectivity": "mesh2d_delaunay_face_nodes",
        },
    )
    data_vars["mesh2d_voronoi"] = xr.DataArray(
        np.int32(0),
        attrs={
            "cf_role": "mesh_topology",
            "long_name": "Voronoi tesselation (dual mesh)",
            "topology_dimension": 2,
            "node_coordinates": "mesh2d_voronoi_node_x mesh2d_voronoi_node_y",
            "edge_node_connectivity": "mesh2d_voronoi_edge_nodes",
            "face_node_connectivity": "mesh2d_voronoi_face_nodes",
        },
    )

    data_vars["mesh2d_delaunay_node_x"] = xr.DataArray(
        np.ascontiguousarray(delaunay["nodes"]["x"].values),
        dims="n_mesh2d_delaunay_node",
        attrs={"standard_name": "projection_x_coordinate", "units": x_units},
    )
    data_vars["mesh2d_delaunay_node_y"] = xr.DataArray(
        np.ascontiguousarray(delaunay["nodes"]["y"].values),
        dims="n_mesh2d_delaunay_node",
        attrs={"standard_name": "projection_y_coordinate", "units": y_units},
    )
    data_vars["mesh2d_voronoi_node_x"] = xr.DataArray(
        np.ascontiguousarray(voronoi["corners"]["x"].values),
        dims="n_mesh2d_voronoi_node",
        attrs={"standard_name": "projection_x_coordinate", "units": x_units},
    )
    data_vars["mesh2d_voronoi_node_y"] = xr.DataArray(
        np.ascontiguousarray(voronoi["corners"]["y"].values),
        dims="n_mesh2d_voronoi_node",
        attrs={"standard_name": "projection_y_coordinate", "units": y_units},
    )

    edge_attrs = {"cf_role": "edge_node_connectivity", "start_index": 0}
    face_attrs = {"cf_role": "face_node_connectivity", "start_index": 0}

    data_vars["mesh2d_delaunay_edge_nodes"] = xr.DataArray(
        np.ascontiguousarray(delaunay["links"][["head", "tail"]].values),
        dims=("n_mesh2d_delaunay_edge", "Two"),
        attrs=dict(edge_attrs),
    )
    data_vars["mesh2d_delaunay_face_nodes"] = xr.DataArray(
        np.ascontiguousarray(delaunay["patches"][["first", "second", "third"]].values),
        dims=("n_mesh2d_delaunay_face", "Three"),
        attrs=dict(face_attrs),
    )
    data_vars["mesh2d_voronoi_edge_nodes"] = xr.DataArray(
        np.ascontiguousarray(voronoi["faces"][["head", "tail"]].values),
        dims=("n_mesh2d_voronoi_edge", "Two"),
        attrs=dict(edge_attrs),
    )
    # Ragged, recomputed on load; written for external tools only.
    data_vars["mesh2d_voronoi_face_nodes"] = xr.DataArray(
        np.ascontiguousarray(grid.corners_at_cell),
        dims=("n_mesh2d_voronoi_face", "n_mesh2d_voronoi_max_face_nodes"),
        attrs=dict(face_attrs),
    )

    data_vars["landlab_node_status"] = xr.DataArray(
        np.ascontiguousarray(grid._node_status),
        dims="n_mesh2d_delaunay_node",
        attrs={
            "long_name": "landlab node boundary-condition status",
            "mesh": "mesh2d_delaunay",
            "location": "node",
        },
    )

    data_vars["landlab_node_bc"] = xr.DataArray(
        np.ascontiguousarray(delaunay["nodes"]["BC"].values.astype(np.int8)),
        dims="n_mesh2d_delaunay_node",
        attrs={
            "long_name": "Triangle boundary marker (0 interior, 1 boundary)",
            "mesh": "mesh2d_delaunay",
            "location": "node",
        },
    )

    for location, (mesh, ugrid_loc) in _LOCATION_TO_MESH.items():
        group = getattr(grid, f"at_{location}")
        dim = _LOCATION_TO_DIM[location]

        # FieldDataset.items() can return empty even when keys() is populated.
        for name in group.keys():
            values = np.asarray(group[name])
            # netCDF has no bool type; store as int8 and tag it for the reader.
            attrs = {"mesh": mesh, "location": ugrid_loc}
            if values.dtype == bool:
                values = values.astype(np.int8)
                attrs["dtype"] = "bool"

            field_units = group.dataset[name].attrs.get("units")
            if field_units is not None:
                attrs["units"] = str(field_units)

            data_vars[f"{name}_at_{location}"] = xr.DataArray(
                np.ascontiguousarray(values), dims=dim, attrs=attrs
            )

    dataset = xr.Dataset(
        data_vars,
        attrs={
            "Conventions": "UGRID-1.0",
            "landlab_triangle_version": _version(),
            "landlab_xy_axis_name": [str(axis_name[0]), str(axis_name[1])],
            "landlab_xy_of_reference": [float(xy_of_reference[0]), float(xy_of_reference[1])],
        },
    )

    # Explicit fill value on every connectivity array (landlab pads with -1).
    encoding = {
        var: {"_FillValue": _FILL_VALUE}
        for var in (
            "mesh2d_delaunay_edge_nodes",
            "mesh2d_delaunay_face_nodes",
            "mesh2d_voronoi_edge_nodes",
            "mesh2d_voronoi_face_nodes",
        )
    }

    dataset.to_netcdf(path, engine="netcdf4", encoding=encoding)

    return str(path)


def read_ugrid(path) -> dict:
    """Read a file written by :func:`write_ugrid`.

    Returns a dict with the ``"delaunay"`` and ``"voronoi"`` dicts the
    construction tail expects, plus ``"node_status"``, ``"units"``,
    ``"axis_name"``, ``"xy_of_reference"``, and ``"fields"``
    (``{location: {name: (array, units)}}``). Raises ``ValueError`` on a file
    that landlab-triangle did not write.
    """
    with xr.open_dataset(path, engine="netcdf4") as dataset:
        dataset = dataset.load()

    if (
        "landlab_triangle_version" not in dataset.attrs
        or "landlab_node_status" not in dataset.variables
    ):
        raise ValueError(
            f"{path!r} is not a landlab-triangle UGRID file: it is missing the "
            "landlab_node_status variable and/or landlab_triangle_version "
            "attribute. Only files written by landlab-triangle can be loaded."
        )

    node_x = dataset["mesh2d_delaunay_node_x"].values
    node_status = np.asarray(dataset["landlab_node_status"].values)

    if "landlab_node_bc" in dataset.variables:
        node_bc = np.asarray(dataset["landlab_node_bc"].values).astype(int)
    else:
        node_bc = (node_status != 0).astype(int)

    # _FillValue makes xarray decode these as float; none are ragged, so the
    # cast back to int is exact.
    delaunay_links = dataset["mesh2d_delaunay_edge_nodes"].values.astype(np.int64)
    delaunay_faces = dataset["mesh2d_delaunay_face_nodes"].values.astype(np.int64)
    voronoi_faces = dataset["mesh2d_voronoi_edge_nodes"].values.astype(np.int64)

    delaunay = {
        "nodes": pd.DataFrame(
            {
                "Node": np.arange(len(node_x)),
                "x": node_x,
                "y": dataset["mesh2d_delaunay_node_y"].values,
                "BC": node_bc,
            }
        ),
        "links": pd.DataFrame(
            {
                "Link": np.arange(len(delaunay_links)),
                "head": delaunay_links[:, 0],
                "tail": delaunay_links[:, 1],
                "BC": 0,
            }
        ),
        "patches": pd.DataFrame(
            {
                "Patch": np.arange(len(delaunay_faces)),
                "first": delaunay_faces[:, 0],
                "second": delaunay_faces[:, 1],
                "third": delaunay_faces[:, 2],
            }
        ),
    }

    corner_x = dataset["mesh2d_voronoi_node_x"].values
    voronoi = {
        "corners": pd.DataFrame(
            {
                "Node": np.arange(len(corner_x)),
                "x": corner_x,
                "y": dataset["mesh2d_voronoi_node_y"].values,
            }
        ),
        "faces": pd.DataFrame(
            {
                "Link": np.arange(len(voronoi_faces)),
                "head": voronoi_faces[:, 0],
                "tail": voronoi_faces[:, 1],
            }
        ),
    }

    fields = {location: {} for location in _LOCATION_TO_MESH}
    reserved = {
        "mesh2d_delaunay",
        "mesh2d_voronoi",
        "mesh2d_delaunay_node_x",
        "mesh2d_delaunay_node_y",
        "mesh2d_voronoi_node_x",
        "mesh2d_voronoi_node_y",
        "mesh2d_delaunay_edge_nodes",
        "mesh2d_delaunay_face_nodes",
        "mesh2d_voronoi_edge_nodes",
        "mesh2d_voronoi_face_nodes",
        "landlab_node_status",
        "landlab_node_bc",
    }

    for name in dataset.variables:
        if name in reserved:
            continue

        variable = dataset[name]
        location = variable.attrs.get("location")
        mesh = variable.attrs.get("mesh")
        if location is None or mesh is None:
            continue

        landlab_location = next(
            (loc for loc, (m, ul) in _LOCATION_TO_MESH.items() if m == mesh and ul == location),
            None,
        )
        if landlab_location is None:
            continue

        suffix = f"_at_{landlab_location}"
        field_name = name[: -len(suffix)] if name.endswith(suffix) else name

        values = np.asarray(variable.values)
        if variable.attrs.get("dtype") == "bool":
            values = values.astype(bool)

        fields[landlab_location][field_name] = (values, variable.attrs.get("units", "-"))

    units = (
        dataset["mesh2d_delaunay_node_x"].attrs.get("units", "-"),
        dataset["mesh2d_delaunay_node_y"].attrs.get("units", "-"),
    )

    axis_name = dataset.attrs.get("landlab_xy_axis_name", ("x", "y"))
    xy_of_reference = dataset.attrs.get("landlab_xy_of_reference", (0.0, 0.0))

    return {
        "delaunay": delaunay,
        "voronoi": voronoi,
        "node_status": node_status,
        "units": units,
        "axis_name": tuple(str(name) for name in axis_name),
        "xy_of_reference": tuple(float(value) for value in xy_of_reference),
        "fields": fields,
    }
