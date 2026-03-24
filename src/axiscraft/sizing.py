from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1 + 5**0.5) / 2
DEFAULT_WH_RATIO = 1 / PHI   # golden ratio ≈ 0.618

PT_TO_CM = 0.03514            # LaTeX points to centimetres
CM_TO_IN = 1 / 2.54           # centimetres to inches

# ---------------------------------------------------------------------------
# Document format registry
# Keys   : format name (str)
# Values : full textwidth in LaTeX points (float)
# ---------------------------------------------------------------------------

DOCUMENT_FORMATS: dict[str, float] = {
    "1col": 487.8225,    # Standard LaTeX article / IEEE single-column textwidth
    "b5":   355.65945,   # B5 thesis textwidth
}


def register_format(name: str, textwidth_pt: float) -> None:
    """Add a custom document format to the registry.

    Parameters
    ----------
    name:
        Identifier used when constructing a Figure (e.g. ``"elsevier"``).
    textwidth_pt:
        Full text-column width in LaTeX points.
    """
    DOCUMENT_FORMATS[name] = textwidth_pt


# ---------------------------------------------------------------------------
# FigureSize
# ---------------------------------------------------------------------------

@dataclass
class FigureSize:
    """Resolved figure dimensions in both inches (for matplotlib) and cm."""

    width_in:  float
    height_in: float
    width_cm:  float
    height_cm: float

    @classmethod
    def from_format(
        cls,
        format: str = "1col",
        columns: int = 1,
        scale: float = 1.0,
        wh_ratio: float = DEFAULT_WH_RATIO,
    ) -> FigureSize:
        """Resolve size from a named document format.

        Parameters
        ----------
        format:
            Key in ``DOCUMENT_FORMATS`` (e.g. ``"1col"``, ``"b5"``).
        columns:
            Integer number of columns the figure spans.  The textwidth is
            divided evenly; for non-integer fractions use ``from_cm`` instead.
        scale:
            Uniform multiplier applied after the column division.  Scales both
            width and height, preserving the aspect ratio.
        wh_ratio:
            Height-to-width ratio.  Defaults to the golden ratio (≈ 0.618).
        """
        if format not in DOCUMENT_FORMATS:
            raise ValueError(
                f"Unknown format '{format}'. "
                f"Available: {list(DOCUMENT_FORMATS)}. "
                "Use register_format() to add a custom format."
            )
        if columns < 1:
            raise ValueError("columns must be >= 1")

        width_cm  = (DOCUMENT_FORMATS[format] * PT_TO_CM / columns) * scale
        height_cm = width_cm * wh_ratio
        return cls(
            width_in=width_cm * CM_TO_IN,
            height_in=height_cm * CM_TO_IN,
            width_cm=width_cm,
            height_cm=height_cm,
        )

    @classmethod
    def from_cm(
        cls,
        width: float,
        wh_ratio: float = DEFAULT_WH_RATIO,
    ) -> FigureSize:
        """Resolve size from an explicit centimetre width.

        Bypasses the format/column system entirely.

        Parameters
        ----------
        width:
            Figure width in centimetres.
        wh_ratio:
            Height-to-width ratio.  Defaults to the golden ratio (≈ 0.618).
        """
        height_cm = width * wh_ratio
        return cls(
            width_in=width * CM_TO_IN,
            height_in=height_cm * CM_TO_IN,
            width_cm=width,
            height_cm=height_cm,
        )

    def __repr__(self) -> str:
        return (
            f"FigureSize("
            f"width={self.width_cm:.2f} cm, "
            f"height={self.height_cm:.2f} cm)"
        )
