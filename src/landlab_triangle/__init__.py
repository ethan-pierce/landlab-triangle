from .mesh import TriangleError
from .triangle import TriangleModelGrid

_PLOTTERS = (
    "plot_cell",
    "plot_corner",
    "plot_face",
    "plot_link",
    "plot_mesh",
    "plot_node",
    "plot_patch",
    "plot_vector",
)

__all__ = ["TriangleError", "TriangleModelGrid", *_PLOTTERS]


def __getattr__(name):
    # Defer the matplotlib import until a plotter is actually used.
    if name in _PLOTTERS:
        from . import plot

        return getattr(plot, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
