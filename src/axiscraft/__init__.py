"""AxisCraft — precise, reproducible matplotlib figure layouts."""

from .figure import Figure
from .sizing import (
    FigureSize,
    register_format,
    DEFAULT_WH_RATIO,
    DOCUMENT_FORMATS,
)

__all__ = [
    "Figure",
    "FigureSize",
    "register_format",
    "DEFAULT_WH_RATIO",
    "DOCUMENT_FORMATS",
]
