"""The frozen v1.0 public surface."""

import landlab_triangle


def test_public_namespace():
    assert set(landlab_triangle.__all__) == {
        "TriangleError",
        "TriangleModelGrid",
        "plot_cell",
        "plot_corner",
        "plot_face",
        "plot_link",
        "plot_mesh",
        "plot_node",
        "plot_patch",
        "plot_vector",
    }


def test_internal_classes_are_not_top_level():
    for name in ("TriangleGraph", "DualTriangleGraph", "TriangleMesh"):
        assert not hasattr(landlab_triangle, name)


def test_plotters_are_importable():
    from landlab_triangle import plot_node, plot_vector

    assert callable(plot_node) and callable(plot_vector)
