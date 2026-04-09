"""Unit tests for the theme parser (theme.py).

Covers parse, update, inject, round-trip, and edge cases.
"""

from __future__ import annotations

from mcp_collateral.theme import (
    THEME_END,
    THEME_START,
    inject_theme,
    parse_theme,
    update_theme,
)

# ---------------------------------------------------------------------------
# Sample source with a full theme block
# ---------------------------------------------------------------------------

FULL_THEME_SOURCE = """\
#set document(title: "Test")

// === THEME ===
#let dark-bg = rgb("#1a1a2e")
#let accent = rgb("#e94560")
#let font-display = "Inter"
#let font-body = "Georgia"
#let gap = 12pt
// === END THEME ===

= Hello World
"""

NO_THEME_SOURCE = """\
#set document(title: "No Theme")
= Hello
"""

# ---------------------------------------------------------------------------
# parse_theme
# ---------------------------------------------------------------------------


class TestParseTheme:
    """parse_theme extracts colors, fonts, spacing, and raw from the block."""

    def test_full_theme_block(self) -> None:
        result = parse_theme(FULL_THEME_SOURCE)
        assert result["colors"]["dark_bg"] == "#1a1a2e"
        assert result["colors"]["accent"] == "#e94560"
        assert result["fonts"]["display"] == "Inter"
        assert result["fonts"]["body"] == "Georgia"
        assert result["spacing"]["gap"] == "12pt"
        assert "dark_bg" in result["raw"]

    def test_no_markers_returns_empty(self) -> None:
        result = parse_theme(NO_THEME_SOURCE)
        assert result["colors"] == {}
        assert result["fonts"] == {}
        assert result["spacing"] == {}
        assert result["raw"] == {}

    def test_hyphenated_names_to_underscored_keys(self) -> None:
        result = parse_theme(FULL_THEME_SOURCE)
        # dark-bg becomes dark_bg
        assert "dark_bg" in result["colors"]
        assert "dark-bg" not in result["colors"]

    def test_raw_contains_original_values(self) -> None:
        result = parse_theme(FULL_THEME_SOURCE)
        assert result["raw"]["dark_bg"] == 'rgb("#1a1a2e")'
        assert result["raw"]["font_display"] == '"Inter"'
        assert result["raw"]["gap"] == "12pt"

    def test_result_has_expected_keys(self) -> None:
        result = parse_theme(FULL_THEME_SOURCE)
        assert set(result.keys()) == {"colors", "fonts", "spacing", "raw"}


# ---------------------------------------------------------------------------
# update_theme
# ---------------------------------------------------------------------------


class TestUpdateTheme:
    """update_theme modifies individual #let values inside the block."""

    def test_change_single_color(self) -> None:
        updated = update_theme(FULL_THEME_SOURCE, {"accent": "#ff0000"})
        result = parse_theme(updated)
        assert result["colors"]["accent"] == "#ff0000"
        # Other values unchanged
        assert result["colors"]["dark_bg"] == "#1a1a2e"

    def test_change_font(self) -> None:
        updated = update_theme(FULL_THEME_SOURCE, {"font-display": '"Helvetica"'})
        result = parse_theme(updated)
        assert result["fonts"]["display"] == "Helvetica"

    def test_underscore_keys_work(self) -> None:
        updated = update_theme(FULL_THEME_SOURCE, {"dark_bg": "#000000"})
        result = parse_theme(updated)
        assert result["colors"]["dark_bg"] == "#000000"

    def test_no_markers_returns_source_unchanged(self) -> None:
        updated = update_theme(NO_THEME_SOURCE, {"accent": "#ff0000"})
        assert updated == NO_THEME_SOURCE

    def test_non_matching_key_leaves_source_unchanged(self) -> None:
        updated = update_theme(FULL_THEME_SOURCE, {"nonexistent": "#aabbcc"})
        result = parse_theme(updated)
        assert result["colors"]["dark_bg"] == "#1a1a2e"


# ---------------------------------------------------------------------------
# inject_theme
# ---------------------------------------------------------------------------


class TestInjectTheme:
    """inject_theme inserts or replaces the entire theme block."""

    def test_inject_into_source_without_markers(self) -> None:
        theme = {"colors": {"primary": "#112233"}, "fonts": {"display": "Arial"}}
        result = inject_theme(NO_THEME_SOURCE, theme)
        assert THEME_START in result
        assert THEME_END in result
        assert '#let primary = rgb("#112233")' in result
        assert '#let font-display = "Arial"' in result
        # Original content preserved
        assert "= Hello" in result

    def test_replace_existing_markers(self) -> None:
        theme = {"colors": {"primary": "#aabbcc"}}
        result = inject_theme(FULL_THEME_SOURCE, theme)
        parsed = parse_theme(result)
        assert parsed["colors"]["primary"] == "#aabbcc"
        # Old colors should be gone
        assert "dark_bg" not in parsed["colors"]

    def test_inject_spacing(self) -> None:
        theme = {"spacing": {"gap": "16pt"}}
        result = inject_theme(NO_THEME_SOURCE, theme)
        parsed = parse_theme(result)
        assert parsed["spacing"]["gap"] == "16pt"


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """parse -> inject preserves values."""

    def test_round_trip_preserves_values(self) -> None:
        parsed = parse_theme(FULL_THEME_SOURCE)
        # Inject the parsed theme into a blank source
        injected = inject_theme(NO_THEME_SOURCE, parsed)
        reparsed = parse_theme(injected)
        assert reparsed["colors"] == parsed["colors"]
        assert reparsed["fonts"] == parsed["fonts"]
        assert reparsed["spacing"] == parsed["spacing"]
