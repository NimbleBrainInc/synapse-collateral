"""Tests for the bundle-side custom-instructions surface (`app://instructions`).

Mirrors the synapse-todo-board pattern. Voice ↔ custom-instructions are the
same body for collateral; these tests exercise the round-trip from voice.md
on disk → `app://instructions` resource → set_voice tool path.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def collateral_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point UPJACK_ROOT at a fresh tmpdir and rebind store's path constants.

    `BASE_DIR` and the derived `*_DIR` constants are resolved at module import
    time, so a `setenv` alone is too late. We patch the module attributes so
    every store function — including `_ensure_dirs` — reads the test path.
    """
    root = tmp_path / "ws"
    monkeypatch.setenv("UPJACK_ROOT", str(root))

    from mcp_collateral import store

    monkeypatch.setattr(store, "BASE_DIR", root)
    monkeypatch.setattr(store, "ASSETS_DIR", root / "assets")
    monkeypatch.setattr(store, "FONTS_DIR", root / "fonts")
    monkeypatch.setattr(store, "TEMPLATES_DIR", root / "templates")
    monkeypatch.setattr(store, "DOCUMENTS_DIR", root / "documents")
    monkeypatch.setattr(store, "COMPILE_DIR", root / "_compile")
    return root


def _voice_path(root: Path) -> Path:
    return root / "voice.md"


class TestAppInstructionsResource:
    """The platform reads `app://instructions` on every prompt assembly."""

    def test_returns_empty_string_when_unset(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        assert ws.get_voice() == ""
        assert not _voice_path(collateral_root).exists()

    def test_returns_saved_body(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        ws.set_voice("# Voice\n\nWrite plainly.")
        assert ws.get_voice() == "# Voice\n\nWrite plainly."
        assert _voice_path(collateral_root).read_text() == "# Voice\n\nWrite plainly."


class TestSetVoiceContract:
    """set_voice mirrors the platform's `app://instructions` write contract."""

    def test_save_returns_status_saved(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        result = ws.set_voice("Some voice")
        assert result["status"] == "saved"
        assert _voice_path(collateral_root).read_text() == "Some voice"

    def test_empty_clears_file(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        ws.set_voice("first")
        assert _voice_path(collateral_root).exists()

        result = ws.set_voice("")
        assert result == {"status": "cleared"}
        assert not _voice_path(collateral_root).exists()
        assert ws.get_voice() == ""

    def test_clear_when_already_empty_is_idempotent(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        result = ws.set_voice("")
        assert result == {"status": "cleared"}
        assert not _voice_path(collateral_root).exists()

    def test_overwrites_existing_voice(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        ws.set_voice("first")
        ws.set_voice("second")
        assert _voice_path(collateral_root).read_text() == "second"


class TestByteCap:
    """8 KiB UTF-8 cap — matches platform's `MAX_INSTRUCTIONS_BYTES`."""

    def test_at_cap_succeeds(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import MAX_VOICE_BYTES, Workspace

        ws = Workspace()
        body = "a" * MAX_VOICE_BYTES  # ASCII → 1 byte per char
        result = ws.set_voice(body)
        assert result["status"] == "saved"

    def test_one_byte_over_raises(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import MAX_VOICE_BYTES, Workspace

        ws = Workspace()
        body = "a" * (MAX_VOICE_BYTES + 1)
        with pytest.raises(ValueError, match=str(MAX_VOICE_BYTES)):
            ws.set_voice(body)
        # On rejection, no partial write should land on disk.
        assert not _voice_path(collateral_root).exists()

    def test_multibyte_utf8_counted_in_bytes_not_chars(
        self, collateral_root: Path
    ) -> None:
        """Each emoji is 4 bytes in UTF-8; a 2049-emoji body is 8196 bytes (>8192).

        Tests that we're enforcing the cap in *bytes*, not character count.
        Otherwise a body with 2049 chars (≪ 8192) would slip through.
        """
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        body = "😀" * 2049
        with pytest.raises(ValueError):
            ws.set_voice(body)


class TestSkillResourceNoLongerSplices:
    """The skill resource used to inline voice — it shouldn't anymore.

    The platform now wraps `app://instructions` in `<app-custom-instructions>`
    containment automatically, so duplicating the voice into the skill body
    is redundant (and would cause double-injection in the agent's context).
    """

    def test_skill_does_not_contain_voice_body(self, collateral_root: Path) -> None:
        from mcp_collateral.workspace import Workspace

        ws = Workspace()
        ws.set_voice("CONFIDENTIAL_VOICE_MARKER")
        # Re-import to pick up the in-test SKILL_CONTENT
        from mcp_collateral.server import collateral_skill

        skill_text = collateral_skill()
        assert "CONFIDENTIAL_VOICE_MARKER" not in skill_text
        # And the placeholder should be stripped — no `<!-- VOICE -->` left.
        assert "<!-- VOICE -->" not in skill_text
