"""Brand configuration, presets, and Typst theme generation."""

from __future__ import annotations

from .models import BrandColors, BrandConfig, BrandFonts, BrandPresetInfo, BrandSpacing
from .store import read_components

PRESETS: dict[str, BrandConfig] = {
    "default": BrandConfig(
        name="Default",
        colors=BrandColors(),
        fonts=BrandFonts(),
        spacing=BrandSpacing(),
    ),
    "corporate": BrandConfig(
        name="Corporate",
        colors=BrandColors(primary="#1E3A5F", accent="#2563EB"),
        fonts=BrandFonts(),
        spacing=BrandSpacing(),
    ),
    "modern": BrandConfig(
        name="Modern",
        colors=BrandColors(primary="#7C3AED", accent="#EC4899"),
        fonts=BrandFonts(),
        spacing=BrandSpacing(),
    ),
    "warm": BrandConfig(
        name="Warm",
        colors=BrandColors(primary="#D97706", accent="#DC2626", ink="#1C1917", dark="#292524"),
        fonts=BrandFonts(),
        spacing=BrandSpacing(),
    ),
    "monochrome": BrandConfig(
        name="Monochrome",
        colors=BrandColors(primary="#000000", accent="#525252"),
        fonts=BrandFonts(),
        spacing=BrandSpacing(),
    ),
}


def list_presets() -> list[BrandPresetInfo]:
    return [
        BrandPresetInfo(
            id=pid,
            name=cfg.name,
            description=f"{cfg.name} brand preset",
            primary_color=cfg.colors.primary,
        )
        for pid, cfg in PRESETS.items()
    ]


def generate_theme_typ(brand: BrandConfig) -> str:
    """Generate _base_theme.typ from a BrandConfig."""
    c = brand.colors
    f = brand.fonts
    s = brand.spacing
    theme = f"""\
// Auto-generated from brand config
#let primary = rgb("{c.primary}")
#let accent = rgb("{c.accent}")
#let ink = rgb("{c.ink}")
#let dark = rgb("{c.dark}")
#let mid = rgb("{c.mid}")
#let subtle = rgb("{c.subtle}")
#let faint = rgb("{c.faint}")
#let wash = rgb("{c.wash}")
#let paper = rgb("{c.paper}")
#let dark-bg = rgb("{c.dark_bg}")
#let dark-surface = rgb("{c.dark_surface}")
#let success-color = rgb("{c.success}")
#let warning-color = rgb("{c.warning}")
#let error-color = rgb("{c.error}")

#let font-display = "{f.display}"
#let font-body = "{f.body}"
#let font-code = "{f.code}"

#let pad-x = {s.pad_x}
#let pad-y = {s.pad_y}
#let section-gap = {s.section_gap}
#let label-gap = {s.label_gap}
#let headline-gap = {s.headline_gap}
#let para-gap = {s.para_gap}
#let card-gap = {s.card_gap}

// Components
#let section-label(label, color: primary) = {{
  text(font: font-display, size: 7.5pt, fill: color, weight: "semibold", tracking: 2pt)[#upper(label)]
}}

#let display-heading(body, size: 22pt) = {{
  text(font: font-display, size: size, fill: ink, weight: "light", tracking: -0.3pt, body)
}}

#let body-text(body) = {{
  set par(leading: 8pt, spacing: 8pt)
  text(font: font-body, size: 9.5pt, fill: mid, body)
}}

#let callout-box(body, accent-color: primary) = {{
  block(
    width: 100%,
    inset: (left: 16pt, right: 16pt, top: 12pt, bottom: 12pt),
    radius: (right: 4pt),
    stroke: (left: 3pt + accent-color),
    fill: wash,
  )[
    #set text(size: 9pt, fill: dark)
    #set par(leading: 7pt)
    #body
  ]
}}
"""

    # Append user-defined components (if any) after the base theme
    components = read_components()
    if components.strip():
        theme += "\n// User-defined components (from brand/components.typ)\n"
        theme += components
        if not components.endswith("\n"):
            theme += "\n"

    return theme
