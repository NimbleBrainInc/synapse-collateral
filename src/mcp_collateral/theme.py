"""Theme parser for Typst source files.

Parses ``// === THEME ===`` blocks from Typst source, categorizes tokens
(colors, fonts, spacing), and writes updates back.  The Typst source is
the single source of truth for theme data.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

THEME_START = "// === THEME ==="
THEME_END = "// === END THEME ==="

_LET_RE = re.compile(r"^#let\s+([\w-]+)\s*=\s*(.+)$")
_RGB_RE = re.compile(r'^rgb\("(#[0-9A-Fa-f]{6})"\)$')
_QUOTED_RE = re.compile(r'^"([^"]*)"$')
_PT_RE = re.compile(r"^(\d+(?:\.\d+)?pt)$")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hyphen_to_underscore(name: str) -> str:
    return name.replace("-", "_")


def _underscore_to_hyphen(name: str) -> str:
    return name.replace("_", "-")


def _find_theme_block(source: str) -> tuple[int | None, int | None]:
    """Return (start, end) line indices of the theme markers, or (None, None)."""
    lines = source.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == THEME_START:
            start = i
        elif stripped == THEME_END:
            end = i
            break
    return start, end


# ---------------------------------------------------------------------------
# parse_theme
# ---------------------------------------------------------------------------


def parse_theme(source: str) -> dict:
    """Extract theme tokens from a Typst source string.

    Looks for a block delimited by ``// === THEME ===`` and
    ``// === END THEME ===``.  Each ``#let`` line inside the block is
    categorized:

    * ``rgb("#RRGGBB")`` -> color (hex string)
    * Quoted ``"string"`` -> font
    * ``Npt`` (number + pt) -> spacing

    Returns ``{"colors": {}, "fonts": {}, "spacing": {}, "raw": {}}``.
    Keys use underscores (``dark_bg``).  ``raw`` maps underscore keys to the
    original Typst RHS value.
    """
    colors: dict[str, str] = {}
    fonts: dict[str, str] = {}
    spacing: dict[str, str] = {}
    raw: dict[str, str] = {}

    start, end = _find_theme_block(source)
    if start is None or end is None:
        return {"colors": colors, "fonts": fonts, "spacing": spacing, "raw": raw}

    lines = source.splitlines()
    for line in lines[start + 1 : end]:
        m = _LET_RE.match(line.strip())
        if not m:
            continue
        name_raw, value_raw = m.group(1), m.group(2).strip()
        key = _hyphen_to_underscore(name_raw)
        raw[key] = value_raw

        # Categorize
        rgb_m = _RGB_RE.match(value_raw)
        if rgb_m:
            colors[key] = rgb_m.group(1)
            continue

        quoted_m = _QUOTED_RE.match(value_raw)
        if quoted_m:
            # Strip common prefixes for a cleaner key:
            # "font-display" -> fonts["display"], "font-body" -> fonts["body"]
            font_key = key.removeprefix("font_")
            fonts[font_key] = quoted_m.group(1)
            continue

        pt_m = _PT_RE.match(value_raw)
        if pt_m:
            spacing[key] = pt_m.group(1)
            continue

    return {"colors": colors, "fonts": fonts, "spacing": spacing, "raw": raw}


# ---------------------------------------------------------------------------
# update_theme
# ---------------------------------------------------------------------------


def update_theme(source: str, updates: dict) -> str:
    """Replace individual ``#let`` values inside the theme block.

    *updates* maps token names (hyphenated **or** underscored) to new values.
    Value interpretation:

    * Hex string (``#RRGGBB``) -> wrapped in ``rgb("...")``
    * Otherwise used as-is (caller controls quoting for fonts/spacing)

    Lines outside the theme block are untouched.
    """
    start, end = _find_theme_block(source)
    if start is None or end is None:
        return source

    # Normalize update keys to hyphenated (Typst convention)
    norm: dict[str, str] = {}
    for k, v in updates.items():
        norm[_underscore_to_hyphen(k)] = v

    lines = source.splitlines()
    new_lines = list(lines)

    for i in range(start + 1, end):
        m = _LET_RE.match(lines[i].strip())
        if not m:
            continue
        name = m.group(1)
        if name not in norm:
            continue
        value = norm[name]
        # Auto-wrap hex colors
        if re.match(r"^#[0-9A-Fa-f]{6}$", value):
            value = f'rgb("{value}")'
        new_lines[i] = f"#let {name} = {value}"

    return "\n".join(new_lines) + ("\n" if source.endswith("\n") else "")


# ---------------------------------------------------------------------------
# inject_theme
# ---------------------------------------------------------------------------


def inject_theme(source: str, theme_dict: dict) -> str:
    """Insert or replace the entire theme block in *source*.

    *theme_dict* has the same shape as ``parse_theme`` output (``colors``,
    ``fonts``, ``spacing``).  If the source already contains theme markers
    they are replaced; otherwise the block is prepended.
    """
    block_lines = [THEME_START]

    for key, hex_val in sorted(theme_dict.get("colors", {}).items()):
        name = _underscore_to_hyphen(key)
        if not hex_val.startswith("#"):
            hex_val = f"#{hex_val}"
        block_lines.append(f'#let {name} = rgb("{hex_val}")')

    for key, font_val in sorted(theme_dict.get("fonts", {}).items()):
        name = _underscore_to_hyphen(key)
        # Prefix with font- if not already prefixed
        if not name.startswith("font-"):
            name = f"font-{name}"
        block_lines.append(f'#let {name} = "{font_val}"')

    for key, sp_val in sorted(theme_dict.get("spacing", {}).items()):
        name = _underscore_to_hyphen(key)
        block_lines.append(f"#let {name} = {sp_val}")

    block_lines.append(THEME_END)
    block = "\n".join(block_lines)

    start, end = _find_theme_block(source)
    if start is not None and end is not None:
        lines = source.splitlines()
        before = lines[:start]
        after = lines[end + 1 :]
        result = "\n".join(before) + ("\n" if before else "") + block + "\n" + "\n".join(after)
        if source.endswith("\n") and not result.endswith("\n"):
            result += "\n"
        return result

    # No existing block -- prepend
    return block + "\n" + source
