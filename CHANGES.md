# Changes

All notable changes to landlab-triangle are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-08-22

First stable release.

### Added

- Build unstructured triangular Landlab grids from a boundary polygon, with
  interior holes and control over mesh quality and resolution.
- Create a grid directly, from a dictionary, or from a vector file (shapefile,
  GeoJSON, GeoPackage, ...).
- Save and load grids as CF-UGRID netCDF for ParaView, QGIS, xarray, and
  uxarray.
- Plot node, link, patch, corner, face, and cell fields, vectors, and the bare
  mesh.

[Unreleased]: https://github.com/ethan-pierce/landlab-triangle/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ethan-pierce/landlab-triangle/releases/tag/v1.0.0
