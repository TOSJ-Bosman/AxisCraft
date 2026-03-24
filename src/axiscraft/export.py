from __future__ import annotations

from pathlib import Path

import matplotlib.figure

VECTOR_FORMATS = {"pdf", "svg", "eps", "ps"}


def export_figure(
    fig: matplotlib.figure.Figure,
    path: str,
    fmt: str = "pdf",
    dpi: int = 300,
    **kwargs,
) -> None:
    """Save *fig* to *path* with publication-friendly defaults.

    Parameters
    ----------
    fig:
        The matplotlib Figure to export.
    path:
        Destination path, with or without extension.  The correct extension
        for *fmt* is appended automatically.
    fmt:
        Output format.  Vector formats (``"pdf"``, ``"svg"``, ``"eps"``,
        ``"ps"``) use ``bbox_inches="tight"`` by default.  Raster formats
        (``"png"``, ``"jpg"``, …) also use *dpi*.
    dpi:
        Dots per inch for raster output.  Ignored for vector formats.
    **kwargs:
        Forwarded to :func:`matplotlib.figure.Figure.savefig`, overriding
        any defaults set here.
    """
    full_path = Path(path).with_suffix(f".{fmt}")
    full_path.parent.mkdir(parents=True, exist_ok=True)

    defaults: dict = {"bbox_inches": "tight", "format": fmt}
    if fmt not in VECTOR_FORMATS:
        defaults["dpi"] = dpi

    defaults.update(kwargs)
    fig.savefig(str(full_path), **defaults)
