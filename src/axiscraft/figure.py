from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.figure

from .sizing import FigureSize, DEFAULT_WH_RATIO
from .grid import compute_axes_positions, normalize_gaps
from .export import export_figure

# Alphabet used for axes identifiers (a), (b), …
_ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# Legend location aliases matching the MATLAB names
_LEGEND_LOC = {
    "southwestcorner": "lower left",
    "northeastcorner": "upper right",
    "NorthEast":       "upper right",
}


def _as_list(iax: int | list[int]) -> list[int]:
    return iax if isinstance(iax, list) else [iax]


class Figure:
    """A matplotlib figure with precise, publication-ready layout control.

    Parameters
    ----------
    fig_nbr:
        matplotlib figure number.  Reusing the same number re-uses the
        existing window (and clears it when *clear* is True).
    axes_grid:
        ``(N_row, N_col)`` — the tile grid the axes are placed on.
    axes:
        Custom axes layout as a list of specs.  Each spec is either an
        ``int`` (single tile) or a ``list[int]`` (merged tiles).  Tile
        indices are **1-based**, row-major::

            1  2  3
            4  5  6

        ``None`` builds a full ``N_row × N_col`` grid automatically.
    format:
        Named document format from the registry (``"1col"``, ``"b5"``, …).
        Ignored when *width_cm* is given.
    width_cm:
        Explicit figure width in centimetres.  When provided, *format*,
        *columns*, and *scale* are ignored.
    columns:
        Integer number of columns the figure spans within the document
        format.  The textwidth is divided evenly.
    scale:
        Uniform size multiplier applied after column division.  Scales
        width and height together, preserving the aspect ratio.
    wh_ratio:
        Height-to-width ratio.  Defaults to the golden ratio (≈ 0.618).
    left_margin, bottom_margin, right_margin, top_margin:
        Outer margins as fractions of the figure size (normalised 0–1).
    gap_row, gap_col:
        Gap between rows / columns as a fraction of the figure size.
        Pass a scalar to use the same gap everywhere, or a list of length
        ``N_row - 1`` / ``N_col - 1`` for per-gap control.
    latex:
        When ``True``, enables ``text.usetex`` and sets a serif font
        family.  Requires a working LaTeX installation.
    xpos, ypos:
        Requested on-screen position in centimetres (best-effort; depends
        on the active matplotlib backend).
    clear:
        Clear the figure on construction (default ``True``).
    """

    def __init__(
        self,
        fig_nbr: int = 1,
        axes_grid: tuple[int, int] = (1, 1),
        axes: list | None = None,
        *,
        format: str = "1col",
        width_cm: float | None = None,
        columns: int = 1,
        scale: float = 1.0,
        wh_ratio: float = DEFAULT_WH_RATIO,
        left_margin: float = 0.05,
        bottom_margin: float = 0.05,
        right_margin: float = 0.05,
        top_margin: float = 0.025,
        gap_row: float | list[float] = 0.05,
        gap_col: float | list[float] = 0.05,
        latex: bool = False,
        xpos: float = 1.0,
        ypos: float = 10.0,
        clear: bool = True,
    ) -> None:
        self.N_row, self.N_col = axes_grid

        # --- Resolve figure size ------------------------------------------
        if width_cm is not None:
            self.size = FigureSize.from_cm(width_cm, wh_ratio=wh_ratio)
        else:
            self.size = FigureSize.from_format(
                format, columns=columns, scale=scale, wh_ratio=wh_ratio
            )

        # --- LaTeX rendering (global rcParams) ----------------------------
        if latex:
            matplotlib.rcParams.update({
                "text.usetex":  True,
                "font.family":  "serif",
            })

        # --- Create / clear figure ----------------------------------------
        self.fig: matplotlib.figure.Figure = plt.figure(fig_nbr)
        if clear:
            self.fig.clf()

        self.fig.patch.set_facecolor("white")
        self.fig.set_size_inches(self.size.width_in, self.size.height_in)

        # --- Screen position (best-effort) --------------------------------
        self._set_screen_position(xpos, ypos)

        # --- Resolve gaps -------------------------------------------------
        self._gap_row = normalize_gaps(gap_row, max(0, self.N_row - 1))
        self._gap_col = normalize_gaps(gap_col, max(0, self.N_col - 1))
        self._margins = (left_margin, bottom_margin, right_margin, top_margin)

        # --- Build axes specs ---------------------------------------------
        if axes is None:
            axes_specs = [[i] for i in range(1, self.N_row * self.N_col + 1)]
        else:
            axes_specs = [s if isinstance(s, list) else [s] for s in axes]

        # --- Compute and create axes --------------------------------------
        positions = compute_axes_positions(
            self.N_row, self.N_col,
            self._margins,
            self._gap_row,
            self._gap_col,
            axes_specs,
        )

        self.ax: list[matplotlib.axes.Axes] = []
        for left, bottom, width, height in positions:
            ax = self.fig.add_axes([left, bottom, width, height])
            ax.grid(True, which="major", linewidth=0.6)
            ax.minorticks_on()
            ax.grid(True, which="minor", linewidth=0.3, alpha=0.5)
            self.ax.append(ax)

    # -----------------------------------------------------------------------
    # Screen position
    # -----------------------------------------------------------------------

    def _set_screen_position(self, x: float, y: float) -> None:
        """Move the figure window to (x, y) in centimetres (best-effort)."""
        try:
            manager = self.fig.canvas.manager
            px = int(x * 28.3465)   # 1 cm ≈ 28.35 px at 72 dpi
            py = int(y * 28.3465)
            manager.window.wm_geometry(f"+{px}+{py}")
        except Exception:
            pass

    def position(self, x: float = 1.0, y: float = 10.0) -> None:
        """Move the figure window to *(x, y)* in centimetres."""
        self._set_screen_position(x, y)

    # -----------------------------------------------------------------------
    # Tick label control
    # -----------------------------------------------------------------------

    def xtick_off(self, iax: int | list[int]) -> None:
        """Hide x-axis tick labels on the given axes."""
        for i in _as_list(iax):
            self.ax[i].tick_params(labelbottom=False)

    def ytick_off(self, iax: int | list[int]) -> None:
        """Hide y-axis tick labels on the given axes."""
        for i in _as_list(iax):
            self.ax[i].tick_params(labelleft=False)

    # -----------------------------------------------------------------------
    # Axis labels
    # -----------------------------------------------------------------------

    def xlabel(self, iax: int | list[int], label: str) -> None:
        """Set the x-axis label on one or more axes."""
        for i in _as_list(iax):
            self.ax[i].set_xlabel(label)

    def ylabel(self, iax: int | list[int], label: str) -> None:
        """Set the y-axis label on one or more axes."""
        for i in _as_list(iax):
            self.ax[i].set_ylabel(label)

    # -----------------------------------------------------------------------
    # Legend
    # -----------------------------------------------------------------------

    def legend(
        self,
        iax: int | list[int],
        *args,
        position: str | None = None,
        **kwargs,
    ) -> matplotlib.legend.Legend | list[matplotlib.legend.Legend]:
        """Add a legend to one or more axes.

        Parameters
        ----------
        iax:
            0-based axes index or list of indices.
        *args:
            Forwarded to :func:`matplotlib.axes.Axes.legend`.
        position:
            Optional location string.  Accepts standard matplotlib ``loc``
            strings as well as ``"southwestcorner"`` and
            ``"northeastcorner"``.
        **kwargs:
            Forwarded to :func:`matplotlib.axes.Axes.legend`.
        """
        if position is not None:
            kwargs.setdefault("loc", _LEGEND_LOC.get(position, position))

        legends = [self.ax[i].legend(*args, **kwargs) for i in _as_list(iax)]
        return legends[0] if len(legends) == 1 else legends

    # -----------------------------------------------------------------------
    # Axes identifiers
    # -----------------------------------------------------------------------

    def add_identifier(
        self,
        position: tuple[float, float] | str = (0.875, 0.9),
        position_change: list[tuple[int, float, float]] | None = None,
    ) -> None:
        """Overlay ``(a)``, ``(b)``, … labels on each axes.

        Parameters
        ----------
        position:
            Normalised axes coordinates ``(x, y)`` for all labels, or the
            string ``"NorthEast"`` for a preset position.
        position_change:
            Override the position for specific axes.  Each entry is a
            tuple ``(axes_index, x, y)`` using 0-based indexing.
        """
        if isinstance(position, str) and position == "NorthEast":
            position = (0.875, 0.925)

        positions = [list(position)] * len(self.ax)

        if position_change:
            for idx, x, y in position_change:
                positions[idx] = [x, y]

        for i, ax in enumerate(self.ax):
            ax.text(
                positions[i][0], positions[i][1],
                f"({_ALPHABET[i]})",
                transform=ax.transAxes,
                ha="center", va="center",
            )

    # -----------------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------------

    def export(self, path: str, fmt: str = "pdf", dpi: int = 300, **kwargs) -> None:
        """Export the figure to a file.

        Parameters
        ----------
        path:
            Destination path without extension.
        fmt:
            ``"pdf"``, ``"svg"``, ``"eps"``, ``"png"``, …
        dpi:
            Resolution for raster formats.
        **kwargs:
            Forwarded to :func:`matplotlib.figure.Figure.savefig`.
        """
        export_figure(self.fig, path, fmt=fmt, dpi=dpi, **kwargs)
