# Roadmap to v1.0

Features and cleanup targeted for a clean, feature-rich, citable v1.0 release.

1. **Community health files** — Add `CITATION.cff`, `CONTRIBUTING.md`,
   `CODE-OF-CONDUCT.md`, `CHANGES.md`, `CREDITS.md`, `SUPPORT.md`, and README
   sections for contact, citation, and funding. Follows the CSDMS
   community-ready standard and supplies the metadata for the DOI.

2. **UGRID export** — Write the grid to CF-UGRID netCDF (primal Delaunay and
   dual Voronoi meshes plus fields) for ParaView, QGIS, xarray, and uxarray.
   Replaces the pickle-only output; drops legacy VTK.

3. **Interior points / constraints** — Let users supply forced interior
   vertices, enforced interior segments, and per-region area constraints, not
   just a boundary polygon. Enables feature-conforming, variable-resolution
   meshes.

4. **Adaptive mesh refinement** — Refine an existing grid from a user-supplied
   field (velocity, error estimate, height above nearest drainage) via
   Triangle's `-r`, with field transfer onto the refined mesh. Builds on #3.

5. **Field-aware plotting** — Plot node, patch, and cell fields with colormaps,
   beyond the current mesh-skeleton view.

6. **Error surfacing** — Restore explicit handling of Triangle's exit code so
   failures report Triangle's own message instead of a missing-file error.
