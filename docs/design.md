# AxisCraft — Software Design Document

## 1. Overview

AxisCraft is a matplotlib wrapper that provides precise, reproducible control over figure layout. It is designed for scientific and engineering publications where figures must conform to journal/thesis column widths, use consistent spacing, and export cleanly to vector formats.

The design mirrors the MATLAB `FIG` class but exploits Python idioms to improve extensibility and separation of concerns.

---

## 2. Architecture

```
AxisCraft/
├── src/
│   └── axiscraft/
│       ├── __init__.py
│       ├── figure.py        # Main Figure class
│       ├── sizing.py        # Figure sizing and preset system
│       ├── grid.py          # Axes grid layout engine
│       └── export.py        # Export utilities
├── docs/
│   └── design.md
└── README.md
```

The main user-facing class is `Figure` (in `figure.py`). It composes the sizing, grid, and export subsystems. Each subsystem is independently testable.

---

## 3. Figure Sizing System (`sizing.py`)

This is the most design-sensitive part. The MATLAB implementation conflates two independent concepts into a single string preset (`'b5-2col'`). The Python version separates them.

### 3.1 Two independent concepts

| Concept | What it defines | Example |
|---|---|---|
| **Document format** | The textwidth of the target document (in pt) | IEEE journal, B5 thesis |
| **Column layout** | How many columns the figure spans | 1, 2 |

These combine to give the figure width. A `scale` factor then uniformly scales the result, and height is derived from a width-to-height ratio.

### 3.2 Unit conversion pipeline

matplotlib uses inches for figure size. The pipeline is:

```
LaTeX points (pt)  →  centimeters (cm)  →  inches (in)
       × 0.03514            ÷ 2.54
```

Constants:
```python
PT_TO_CM = 0.03514   # LaTeX pt to cm (matches original MATLAB value)
CM_TO_IN = 1 / 2.54
PT_TO_IN = PT_TO_CM * CM_TO_IN
```

### 3.3 Document format registry

Document formats are stored in a dict keyed by name. Each entry stores the document textwidth in pt. This registry is defined at module level and is user-extensible.

```python
DOCUMENT_FORMATS: dict[str, float] = {
    "1col":  487.8225,   # Default LaTeX article/IEEE (full textwidth)
    "b5":    355.65945,  # B5 thesis textwidth
}
```

A user can register custom formats:
```python
axiscraft.register_format("elsevier", textwidth_pt=483.69684)
```

### 3.4 FigureSize dataclass

The sizing system produces a `FigureSize` object — a plain dataclass holding the resolved dimensions. This separates size computation from figure construction and makes sizes inspectable and reusable.

```python
@dataclass
class FigureSize:
    width_in:  float   # Final width in inches (for matplotlib)
    height_in: float   # Final height in inches (for matplotlib)
    width_cm:  float   # For reference/debugging
    height_cm: float
```

### 3.5 Size resolution logic

The `resolve_size()` function (or classmethod) takes user inputs and returns a `FigureSize`. Accepted input forms:

| `width` argument | Meaning |
|---|---|
| `"1col"` | Full textwidth of the `"1col"` format, 1 column |
| `"b5"` | Full textwidth of the `"b5"` format, 1 column |
| `float` or `int` | Explicit width in cm |

The `columns` argument (default `1`) is an integer that divides the format textwidth evenly. Fractional column widths are not supported — use an explicit cm width instead.

The `scale` argument (default `1.0`) is a uniform multiplier applied after the column division. It scales both width and height together, preserving the aspect ratio. This is useful for quick size adjustments without changing the format or ratio.

```
final_width_cm = (textwidth_cm / columns) * scale
```

Height is always derived:
```python
height_cm = width_cm * wh_ratio
```

The default `wh_ratio` is the golden ratio (`1/φ ≈ 0.618`), which gives visually balanced figures without manual tuning.

### 3.6 Public API sketch

```python
PHI = (1 + 5**0.5) / 2
DEFAULT_WH_RATIO = 1 / PHI  # ≈ 0.618

# From a named format — golden ratio height by default
size = FigureSize.from_format("1col")
size = FigureSize.from_format("1col", columns=2)
size = FigureSize.from_format("b5",   columns=2, scale=0.9)

# Override aspect ratio explicitly
size = FigureSize.from_format("1col", wh_ratio=0.5)

# From an explicit cm width — bypasses the format/column system entirely
size = FigureSize.from_cm(width=8.5)
size = FigureSize.from_cm(width=8.5, wh_ratio=0.5)

# Inspect resolved dimensions
print(size.width_cm, size.height_cm)
```

### 3.7 Screen position

Screen position (`xpos`, `ypos` in cm) is separate from figure size and is passed directly to matplotlib's `fig.canvas.manager` or `set_window_geometry` at figure construction time. It does not belong in `FigureSize`.

---

## 4. Axes Grid System (`grid.py`)

> Full design to follow. Sketch only.

The grid engine takes `N_row`, `N_col`, margins, and gap sizes and computes normalized `[left, bottom, width, height]` positions for each axes — exactly as in the MATLAB version. These are passed directly to `fig.add_axes(...)`.

Key improvement over MATLAB: axes spanning is specified by passing a list of tile indices (same as MATLAB), but the spanning logic will be extracted into a dedicated, testable function.

---

## 5. Main Figure Class (`figure.py`)

`Figure` is the user-facing class. It owns the matplotlib `fig` object, the list of `ax` objects, and delegates to the sizing and grid subsystems.

```python
fig = Figure(
    fig_nbr   = 1,
    axes_grid = (2, 2),
    format    = "1col",   # named preset, or omit and use width_cm
    columns   = 1,
    scale     = 1.0,
    wh_ratio  = 0.618,    # defaults to golden ratio
    latex     = True,
)
```

LaTeX rendering is a constructor flag. When `True`, sets `rcParams["text.usetex"] = True` and configures the pgf backend if available. When `False`, uses matplotlib mathtext.

---

## 6. Export System (`export.py`)

Wraps `fig.savefig()` with sensible defaults for publication output:

```python
fig.export("output/figure1", fmt="pdf")
fig.export("output/figure1", fmt="png", dpi=300)
```

Vector formats (`pdf`, `svg`, `eps`) should set `bbox_inches="tight"` by default. For reproducibility, metadata (author, date) can optionally be embedded.

---

## 7. Design Decisions Summary

| Decision | Choice | Reason |
|---|---|---|
| Backend | matplotlib only | Direct access to normalized axes positioning |
| Size unit | inches internally, cm for user API | matplotlib requires inches; cm is intuitive for users |
| Presets | Registry dict, user-extensible | Avoids hardcoding every journal format |
| Format × columns | Separate arguments | Composable; avoids combinatorial preset explosion |
| `columns` | Integer only | Fractional spans are handled via explicit cm width |
| `scale` | Uniform float multiplier | Allows quick size tweaks without changing format or ratio |
| Default `wh_ratio` | Golden ratio (`1/φ ≈ 0.618`) | Visually balanced without manual tuning |
| LaTeX rendering | Constructor flag | `usetex=True` is slow and requires external install |
| `FigureSize` | Separate dataclass | Decouples size logic from figure construction; testable |
