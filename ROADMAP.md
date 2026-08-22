# Roadmap

landlab-triangle 1.0 is released. Planned work beyond it:

1. **Interior points / constraints** — Let users supply forced interior
   vertices, enforced interior segments, and per-region area constraints, not
   just a boundary polygon. Enables feature-conforming, variable-resolution
   meshes.

2. **Adaptive mesh refinement** — Refine an existing grid from a user-supplied
   field (velocity, error estimate, height above nearest drainage) via
   Triangle's `-r`, with field transfer onto the refined mesh. Builds on #1.

## Known issues

- **Zero-length faces on symmetric domains** — Axis-aligned or otherwise
  symmetric boundaries produce cocircular nodes, yielding zero-length Voronoi
  faces that abort construction with `RuntimeError: triangle has generated a
  graph that contains zero-length face` (graph.py). A plain square fails at
  every area constraint; a rectangle survives only at a couple of coarse `a`
  values. Any interior hole or slight irregularity breaks the symmetry and
  works. Perturb symmetric inputs or collapse degenerate faces so simple
  domains just work. The README examples sidestep this with an irregular
  example polygon.
