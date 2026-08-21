# landlab-triangle

[**View Landlab Documentation**](https://landlab.readthedocs.io/)

[**View triangle Documentation**](https://www.cs.cmu.edu/~quake/triangle.html)

This repository adds `TriangleModelGrid`, a new Landlab grid type that enables unstructured triangular meshes. Unlike Landlab's standard structured grids, `TriangleModelGrid` allows for complex geometries with irregular boundaries, interior holes, and variable grid resolution.

Uses Jonathan Shewchuk's Triangle software.

## Installation

### Installing from PyPI

```bash
pip install landlab-triangle
```

A compiled build of Triangle ships inside the wheel, so there is nothing else
to install. See [`NOTICE`](NOTICE) for the terms of the bundled Triangle, which
remains under Jonathan Shewchuk's non-commercial license.

## Usage

### Option 1: direct initialization

```python
from landlab_triangle import TriangleModelGrid
import numpy as np

# Create a grid directly with exterior coordinates and optional holes
exterior_y = [-1.0, -1.0, 11.0, 11.0]
exterior_x = [0.0, 10.0, 10.0, 0.0]

holes = np.array([[5.0, 5.0]])  # Optional: define interior holes

grid = TriangleModelGrid(
    exterior_y_and_x=(exterior_y, exterior_x),
    holes=holes,
    triangle_opts="pqa1Devjz"
)

print(f"Number of nodes: {grid.number_of_nodes}")
print(f"Number of cells: {grid.number_of_cells}")
print(f"Number of holes: {len(grid._holes)}")
```

### Option 2: from a dictionary

```python
from landlab_triangle import TriangleModelGrid

# Create a grid from a dictionary with "x" and "y" keys
grid_params = {
    "x": [0.0, 10.0, 10.0, 0.0],
    "y": [0.0, 0.0, 10.0, 10.0],
    "triangle_opts": "pqDevjz"
}

grid = TriangleModelGrid.from_dict(grid_params)
```

### Option 3: from a shapefile

```python
from landlab_triangle import TriangleModelGrid

# Create a grid from a shapefile, GeoJSON, or other supported format
grid = TriangleModelGrid.from_shapefile(
    "path/to/polygon.geojson",
    triangle_opts="pqDevjz",
    timeout=10
)

# The grid automatically handles holes defined in the input file
print(f"Number of holes: {len(grid._holes)}")
```

## Triangle options

The `triangle_opts` parameter controls the behavior of the Triangle meshing software. Common options include:

- **q**: Quality mesh generation - ensures no angles smaller than N degrees (defaults to 20)
- **a**: Area constraint - limits the maximum area of triangles

**Timeout**: The `timeout` parameter (in seconds) prevents the meshing process from running indefinitely if Triangle encounters complex geometries.

### Example with area constraint

```python
# Create a grid with maximum triangle area of 0.1
grid = TriangleModelGrid(
    exterior_y_and_x=(exterior_y, exterior_x),
    triangle_opts="pqa0.1Devjz"  # 'a0.1' sets max area to 0.1
)
```

## Plotting

Field-aware plotters live in `landlab_triangle` as free functions that take the
grid first and draw on the current axes (or one you pass as `ax=`). Each returns
the matplotlib artist, so a bare call followed by `plt.show()` just works.

There is one plotter per grid element — `plot_node`, `plot_link`, `plot_patch`,
`plot_corner`, `plot_face`, `plot_cell` — plus `plot_vector` for components and
`plot_mesh` for the bare skeleton. The value argument accepts either a
field-name string or a raw array.

```python
import matplotlib.pyplot as plt
from landlab_triangle import TriangleModelGrid, plot_node, plot_cell, plot_vector

grid = TriangleModelGrid(
    ([-1.0, -1.0, 11.0, 11.0], [0.0, 10.0, 10.0, 0.0]), triangle_opts="pqa1Devjz"
)
grid.add_field("elevation", grid.x_of_node + grid.y_of_node, at="node")

# Smooth node field over the full domain, including perimeter nodes
plot_node(grid, "elevation", cmap="terrain", colorbar_label="elevation (m)")
plt.show()

# Flat-colored Voronoi cells from a raw array
import numpy as np
plot_cell(grid, np.arange(grid.number_of_cells, dtype=float))
plt.show()

# Component vectors as arrows colored by magnitude
u = np.ones(grid.number_of_nodes)
plot_vector(grid, u, u, at="node")
plt.show()
```

Common matplotlib keywords (`vmin`, `vmax`, `norm`, `alpha`, `shading`, ...)
pass straight through to the underlying call. `plot_node` defaults to Gouraud
shading; pass `shading="flat"` for per-triangle color instead.

To reconstruct a vector from flux-at-links, map the link components to nodes
with Landlab's mappers (e.g. `map_link_vector_components_to_node`) first, then
call `plot_vector` on the results.
