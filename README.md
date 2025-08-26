# Landlab Triangle

Uses Jonathan Shewchuk's Triangle software to generate unstructured Landlab grids.

## Installation

### Installing from PyPI

```bash
pip install triangle landlab-triangle
```

### Installing from conda-forge

```bash
conda install -c conda-forge triangle landlab-triangle
```

## Usage

### Constructor 1: Direct Initialization

```python
from lltriangle import TriangleModelGrid
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

### Constructor 2: from_dict Class Method

```python
from lltriangle import TriangleModelGrid

# Create a grid from a dictionary with "x" and "y" keys
grid_params = {
    "x": [0.0, 10.0, 10.0, 0.0],
    "y": [0.0, 0.0, 10.0, 10.0],
    "triangle_opts": "pqDevjz"
}

grid = TriangleModelGrid.from_dict(grid_params)
```

### Constructor 3: from_shapefile Class Method

```python
from lltriangle import TriangleModelGrid

# Create a grid from a shapefile, GeoJSON, or other supported format
grid = TriangleModelGrid.from_shapefile(
    "path/to/polygon.geojson",
    triangle_opts="pqDevjz",
    timeout=10
)

# The grid automatically handles holes defined in the input file
print(f"Number of holes: {len(grid._holes)}")
```

## Triangle Options

The `triangle_opts` parameter controls the behavior of the Triangle meshing software. Common options include:

- **q**: Quality mesh generation - ensures no angles smaller than N degrees
- **a**: Area constraint - limits the maximum area of triangles

**Timeout**: The `timeout` parameter (in seconds) prevents the meshing process from running indefinitely if Triangle encounters complex geometries.

### Example with Area Constraint

```python
# Create a grid with maximum triangle area of 0.1
grid = TriangleModelGrid(
    exterior_y_and_x=(exterior_y, exterior_x),
    triangle_opts="pqa0.1Devjz"  # 'a0.1' sets max area to 0.1
)
```
