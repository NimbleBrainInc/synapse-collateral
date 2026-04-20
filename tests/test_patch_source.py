"""Unit tests for patch_source — structured result contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_collateral.models import PatchSourceResult
from mcp_collateral.workspace import Workspace


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Workspace:
    """Create a workspace with isolated storage."""
    monkeypatch.setattr("mcp_collateral.store.BASE_DIR", tmp_path)
    monkeypatch.setattr("mcp_collateral.store.ASSETS_DIR", tmp_path / "assets")
    monkeypatch.setattr("mcp_collateral.store.FONTS_DIR", tmp_path / "fonts")
    monkeypatch.setattr("mcp_collateral.store.TEMPLATES_DIR", tmp_path / "templates")
    monkeypatch.setattr("mcp_collateral.store.DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr("mcp_collateral.store.COMPILE_DIR", tmp_path / "_compile")

    import mcp_collateral.templates as tmod

    monkeypatch.setattr(tmod, "_seeded", False)

    from mcp_collateral import store

    store._ensure_dirs()
    store.seed_templates()

    return Workspace()


class TestPatchSourceSuccess:
    """Happy-path single and batch edits."""

    def test_single_patch_returns_applied_compiled(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello World\nSome text here.")
        result = workspace.patch_source("Hello World", "Goodbye World")
        assert isinstance(result, PatchSourceResult)
        assert result.applied is True
        assert result.compiled is True
        assert result.reason is None
        assert result.workspace is not None
        assert "Goodbye World" in workspace.source

    def test_batch_patch_returns_applied_compiled(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Title\nLine A\nLine B")
        result = workspace.patch_source_batch(
            [
                {"find": "Title", "replace": "New Title"},
                {"find": "Line A", "replace": "Line X"},
            ]
        )
        assert result.applied is True
        assert result.compiled is True
        assert "New Title" in workspace.source
        assert "Line X" in workspace.source


class TestTextNotFound:
    """reason='text_not_found' — no raise, structured response."""

    def test_single_not_found_returns_structured_failure(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello\nSome text here.")
        result = workspace.patch_source("MISSING TEXT", "replacement")
        assert result.applied is False
        assert result.compiled is False
        assert result.reason == "text_not_found"
        assert result.query == "MISSING TEXT"
        assert result.suggestion is not None
        # Source unchanged
        assert "MISSING TEXT" not in workspace.source

    def test_close_typo_yields_nearest_match(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source(
            "#image(\"/assets/matt-headshot.jpg\", width: 44pt)\n"
            "= Section\n"
            "Body text here.\n"
        )
        # Typo: the agent thinks the image is a PNG
        result = workspace.patch_source(
            '#image("/assets/matt-headshot-circle.png", width: 44pt)',
            '#image("/assets/matt-headshot-new.jpg", width: 44pt)',
        )
        assert result.applied is False
        assert result.reason == "text_not_found"
        assert result.nearest_match is not None
        assert result.nearest_match.similarity >= 0.6
        assert "matt-headshot.jpg" in result.nearest_match.context
        # Context includes line numbers
        assert "│" in result.nearest_match.context

    def test_no_close_match_returns_no_nearest(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Title\nA\nB\n")
        result = workspace.patch_source(
            "this is a completely unrelated search query that does not resemble anything",
            "x",
        )
        assert result.applied is False
        assert result.reason == "text_not_found"
        assert result.nearest_match is None
        assert "get_source" in (result.suggestion or "")

    def test_batch_not_found_reports_failed_edit_index(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Title\nLine A\nLine B")
        result = workspace.patch_source_batch(
            [
                {"find": "Line A", "replace": "Line X"},
                {"find": "NONEXISTENT TEXT", "replace": "oops"},
            ]
        )
        assert result.applied is False
        assert result.reason == "text_not_found"
        assert result.failed_edit_index == 1
        # Rollback: the successful first edit is NOT committed
        assert "Line A" in workspace.source
        assert "Line X" not in workspace.source


class TestCompileError:
    """reason='compile_error' — edit found, Typst rejected; rollback preserved."""

    VALID_SOURCE = "= Hello World\nSome text here."

    def test_single_compile_error_reports_reason_and_rolls_back(
        self, workspace: Workspace
    ) -> None:
        workspace.create_document("Test")
        workspace.set_source(self.VALID_SOURCE)
        result = workspace.patch_source("Hello World", "#let broken = ")
        assert result.applied is False
        assert result.compiled is False
        assert result.reason == "compile_error"
        assert result.compile_error
        # Source rolled back
        assert workspace.source == self.VALID_SOURCE

    def test_batch_compile_error_rolls_back_all_edits(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source(self.VALID_SOURCE)
        result = workspace.patch_source_batch(
            [
                {"find": "Some text", "replace": "Different text"},
                {"find": "Hello World", "replace": "#let broken = "},
            ]
        )
        assert result.applied is False
        assert result.reason == "compile_error"
        # Full rollback
        assert workspace.source == self.VALID_SOURCE

    def test_source_usable_after_compile_error_rollback(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source(self.VALID_SOURCE)
        bad = workspace.patch_source("Some text here.", "#[unclosed")
        assert bad.applied is False
        assert bad.reason == "compile_error"
        # Original source survives; a clean edit still works
        good = workspace.patch_source("Some text here.", "Updated text.")
        assert good.applied is True
        assert good.compiled is True
        assert "Updated text." in workspace.source


class TestValidateFalse:
    """validate=False stages edits without compiling."""

    def test_validate_false_skips_compile_on_single(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello\nSome text.")
        # An edit that would break compilation — but we skip compile
        result = workspace.patch_source(
            "Some text.",
            "#let broken = ",
            validate=False,
        )
        assert result.applied is True
        assert result.compiled is False
        assert result.reason is None
        assert result.compile_error is None
        assert "#let broken = " in workspace.source

    def test_validate_false_skips_compile_on_batch(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Title\nA\nB\n")
        result = workspace.patch_source_batch(
            [
                {"find": "A", "replace": "#let half = "},
                {"find": "B", "replace": "Z"},
            ],
            validate=False,
        )
        assert result.applied is True
        assert result.compiled is False

    def test_validate_false_still_reports_text_not_found(
        self, workspace: Workspace
    ) -> None:
        """Not-found is a precondition for the edit, independent of compile."""
        workspace.create_document("Test")
        workspace.set_source("= Hello")
        result = workspace.patch_source("NOPE", "x", validate=False)
        assert result.applied is False
        assert result.reason == "text_not_found"


class TestNearestMatchContext:
    """The ±3-line context window with line-number gutter."""

    def test_context_shows_relevant_region_for_long_doc(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        # Long document: head, many filler lines, then the target near the end.
        head = "= Document Title\n"
        filler = "\n".join(f"Filler line {i}" for i in range(50))
        target_line = "The quick brown fox jumps over the lazy dog."
        workspace.set_source(f"{head}{filler}\n= Final Section\n{target_line}\n")
        result = workspace.patch_source(
            "The quick brown fox jumps over the lazy dgo.",
            "fixed",
        )
        assert result.applied is False
        assert result.nearest_match is not None
        # Match points near the end, not line 1
        assert result.nearest_match.line > 40
        # Context shows the ending, not the head
        assert "quick brown fox" in result.nearest_match.context
        assert "Document Title" not in result.nearest_match.context

    def test_context_includes_line_numbers(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Alpha\n= Beta\n= Gamma\n")
        result = workspace.patch_source("= Betaa", "= Beta2")
        assert result.nearest_match is not None
        # Line number gutter present (box-drawing pipe)
        assert "│" in result.nearest_match.context


class TestServerCoercion:
    """Server-level JSON string coercion for the edits parameter."""

    def test_json_string_parsed_to_list(self) -> None:
        import json

        edits_str = json.dumps(
            [
                {"find": "old", "replace": "new"},
                {"find": "foo", "replace": "bar"},
            ]
        )
        assert isinstance(edits_str, str)
        parsed = json.loads(edits_str)
        assert isinstance(parsed, list)
        assert parsed[0]["find"] == "old"


class TestInputValidation:
    """Programming-error inputs still raise (these aren't LLM contract cases)."""

    def test_empty_find_raises(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello")
        with pytest.raises(ValueError, match="non-empty"):
            workspace.patch_source("", "x")

    def test_empty_edits_list_raises(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello")
        with pytest.raises(ValueError, match="non-empty"):
            workspace.patch_source_batch([])

    def test_batch_entry_missing_find_raises(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello")
        with pytest.raises(ValueError, match="non-empty"):
            workspace.patch_source_batch([{"replace": "x"}])
