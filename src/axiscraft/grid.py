from __future__ import annotations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_gaps(gap: float | list[float], count: int) -> list[float]:
    """Expand a scalar gap value to a list of length *count*."""
    if isinstance(gap, (int, float)):
        return [float(gap)] * count
    if len(gap) != count:
        raise ValueError(f"Expected {count} gap values, got {len(gap)}.")
    return [float(g) for g in gap]


# ---------------------------------------------------------------------------
# Core layout engine
# ---------------------------------------------------------------------------

def compute_axes_positions(
    N_row: int,
    N_col: int,
    margins: tuple[float, float, float, float],
    gap_row: list[float],
    gap_col: list[float],
    axes_specs: list[list[int]],
) -> list[tuple[float, float, float, float]]:
    """Compute normalised ``[left, bottom, width, height]`` for each axes spec.

    Coordinates are in matplotlib's normalised figure space (0–1).

    Parameters
    ----------
    N_row, N_col:
        Grid dimensions.
    margins:
        ``(left, bottom, right, top)`` as fractions of the figure size.
    gap_row:
        Gaps between rows, length ``N_row - 1``.
    gap_col:
        Gaps between columns, length ``N_col - 1``.
    axes_specs:
        Each element is a list of **1-based** tile indices that form one axes.
        Tiles are numbered row-major, left-to-right then top-to-bottom::

            1  2  3
            4  5  6

        A single-tile axes is ``[1]``; spanning tiles 1 and 2 is ``[1, 2]``.
    """
    margin_left, margin_bottom, margin_right, margin_top = margins

    plot_width  = 1.0 - margin_left - margin_right
    plot_height = 1.0 - margin_top  - margin_bottom

    ax_width  = (plot_width  - sum(gap_col)) / N_col
    ax_height = (plot_height - sum(gap_row)) / N_row

    positions = []
    for spec in axes_specs:
        # 0-based column and row index of every tile in this spec
        cols = [(t - 1) % N_col for t in spec]
        rows = [(t - 1) // N_col for t in spec]

        min_col = min(cols)
        max_col = max(cols)
        min_row = min(rows)
        max_row = max(rows)
        n_cols  = max_col - min_col + 1
        n_rows  = max_row - min_row + 1

        # Left edge: margin + preceding columns + preceding column gaps
        left = margin_left + min_col * ax_width + sum(gap_col[:min_col])

        # Bottom edge (y=0 is figure bottom):
        # start at top of plot area, step down (max_row + 1) full cell heights
        # and all gaps up to (but not including) max_row
        bottom = (
            1.0
            - margin_top
            - (max_row + 1) * ax_height
            - sum(gap_row[:max_row])
        )

        # Width and height include internal gaps swallowed by the span
        width  = n_cols * ax_width  + sum(gap_col[min_col : min_col + n_cols - 1])
        height = n_rows * ax_height + sum(gap_row[min_row : min_row + n_rows - 1])

        positions.append((left, bottom, width, height))

    return positions
