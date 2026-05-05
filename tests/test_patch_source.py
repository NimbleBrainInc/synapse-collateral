"""Unit tests for patch_source — structured result contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_collateral import documents
from mcp_collateral.models import PatchSourceResult


@pytest.fixture()
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point all storage roots at tmp_path."""
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
    return tmp_path


def _read_source(storage: Path, doc_id: str) -> str:
    return (storage / "documents" / doc_id / "source.typ").read_text()


class TestPatchSourceSuccess:
    """Happy-path single and batch edits."""

    def test_single_patch_returns_applied_compiled(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Hello World\nSome text here.")
        result = documents.patch_source("test", "Hello World", "Goodbye World")
        assert isinstance(result, PatchSourceResult)
        assert result.applied is True
        assert result.compiled is True
        assert result.reason is None
        assert result.document is not None
        assert "Goodbye World" in _read_source(isolated_storage, "test")

    def test_batch_patch_returns_applied_compiled(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Title\nLine A\nLine B")
        result = documents.patch_source_batch(
            "test",
            [
                {"find": "Title", "replace": "New Title"},
                {"find": "Line A", "replace": "Line X"},
            ],
        )
        assert result.applied is True
        assert result.compiled is True
        src = _read_source(isolated_storage, "test")
        assert "New Title" in src
        assert "Line X" in src

    def test_document_field_reflects_post_edit_state(self, isolated_storage: Path) -> None:
        """On success, PatchSourceResult.document is the NEW state, not stale.

        The UI reads result.document to refresh its display; a regression
        that returned the pre-edit snapshot would go unnoticed until the
        UI looked visibly wrong.
        """
        documents.create("Test")
        # Include a theme block so get_state has something non-trivial to parse.
        original = (
            "// === THEME ===\n"
            '#let primary = rgb("#000000")\n'
            "// === END THEME ===\n"
            "= Original Heading\n"
        )
        documents.set_source("test", original)
        result = documents.patch_source("test", "= Original Heading", "= Revised Heading")
        assert result.applied is True
        assert result.document is not None
        # Post-edit state is what the caller sees
        src = _read_source(isolated_storage, "test")
        assert "Revised Heading" in src
        assert "Original Heading" not in src
        # The returned document reflects the same document we just edited
        assert result.document.document_name == "Test"

    def test_batch_edits_apply_sequentially(self, isolated_storage: Path) -> None:
        """Edit N can find text that edit N-1 created — the docstring promises this."""
        documents.create("Test")
        documents.set_source("test", "= Alpha\nBody.\n")
        result = documents.patch_source_batch(
            "test",
            [
                # First edit creates "Beta"
                {"find": "Alpha", "replace": "Beta"},
                # Second edit finds "Beta" (only exists because edit 1 ran)
                {"find": "= Beta", "replace": "= Gamma"},
            ],
        )
        assert result.applied is True
        assert result.compiled is True
        src = _read_source(isolated_storage, "test")
        assert "= Gamma" in src
        assert "Alpha" not in src
        assert "Beta" not in src


class TestTextNotFound:
    """reason='text_not_found' — no raise, structured response."""

    def test_single_not_found_returns_structured_failure(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Hello\nSome text here.")
        result = documents.patch_source("test", "MISSING TEXT", "replacement")
        assert result.applied is False
        assert result.compiled is False
        assert result.reason == "text_not_found"
        assert result.query == "MISSING TEXT"
        assert result.suggestion is not None
        # Source unchanged
        assert "MISSING TEXT" not in _read_source(isolated_storage, "test")

    def test_close_typo_yields_nearest_match(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source(
            "test",
            '#image("/assets/matt-headshot.jpg", width: 44pt)\n= Section\nBody text here.\n',
        )
        # Typo: the agent thinks the image is a PNG
        result = documents.patch_source(
            "test",
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

    def test_no_close_match_returns_no_nearest(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Title\nA\nB\n")
        result = documents.patch_source(
            "test",
            "this is a completely unrelated search query that does not resemble anything",
            "x",
        )
        assert result.applied is False
        assert result.reason == "text_not_found"
        assert result.nearest_match is None
        assert "get_source" in (result.suggestion or "")

    def test_batch_not_found_reports_failed_edit_index(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Title\nLine A\nLine B")
        result = documents.patch_source_batch(
            "test",
            [
                {"find": "Line A", "replace": "Line X"},
                {"find": "NONEXISTENT TEXT", "replace": "oops"},
            ],
        )
        assert result.applied is False
        assert result.reason == "text_not_found"
        assert result.failed_edit_index == 1
        # Rollback: the successful first edit is NOT committed
        src = _read_source(isolated_storage, "test")
        assert "Line A" in src
        assert "Line X" not in src


class TestCompileError:
    """reason='compile_error' — edit found, Typst rejected; rollback preserved."""

    VALID_SOURCE = "= Hello World\nSome text here."

    def test_single_compile_error_reports_reason_and_rolls_back(
        self, isolated_storage: Path
    ) -> None:
        documents.create("Test")
        documents.set_source("test", self.VALID_SOURCE)
        result = documents.patch_source("test", "Hello World", "#let broken = ")
        assert result.applied is False
        assert result.compiled is False
        assert result.reason == "compile_error"
        assert result.compile_error
        # Source rolled back
        assert _read_source(isolated_storage, "test") == self.VALID_SOURCE

    def test_batch_compile_error_rolls_back_all_edits(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", self.VALID_SOURCE)
        result = documents.patch_source_batch(
            "test",
            [
                {"find": "Some text", "replace": "Different text"},
                {"find": "Hello World", "replace": "#let broken = "},
            ],
        )
        assert result.applied is False
        assert result.reason == "compile_error"
        # Full rollback
        assert _read_source(isolated_storage, "test") == self.VALID_SOURCE

    def test_source_usable_after_compile_error_rollback(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", self.VALID_SOURCE)
        bad = documents.patch_source("test", "Some text here.", "#[unclosed")
        assert bad.applied is False
        assert bad.reason == "compile_error"
        # Original source survives; a clean edit still works
        good = documents.patch_source("test", "Some text here.", "Updated text.")
        assert good.applied is True
        assert good.compiled is True
        assert "Updated text." in _read_source(isolated_storage, "test")


class TestValidateFalse:
    """validate=False stages edits without compiling."""

    def test_validate_false_skips_compile_on_single(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Hello\nSome text.")
        # An edit that would break compilation — but we skip compile
        result = documents.patch_source(
            "test",
            "Some text.",
            "#let broken = ",
            validate=False,
        )
        assert result.applied is True
        assert result.compiled is False
        assert result.reason is None
        assert result.compile_error is None
        assert "#let broken = " in _read_source(isolated_storage, "test")

    def test_validate_false_skips_compile_on_batch(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Title\nA\nB\n")
        result = documents.patch_source_batch(
            "test",
            [
                {"find": "A", "replace": "#let half = "},
                {"find": "B", "replace": "Z"},
            ],
            validate=False,
        )
        assert result.applied is True
        assert result.compiled is False

    def test_validate_false_still_reports_text_not_found(self, isolated_storage: Path) -> None:
        """Not-found is a precondition for the edit, independent of compile."""
        documents.create("Test")
        documents.set_source("test", "= Hello")
        result = documents.patch_source("test", "NOPE", "x", validate=False)
        assert result.applied is False
        assert result.reason == "text_not_found"


class TestNearestMatchContext:
    """The ±3-line context window with line-number gutter."""

    def test_context_shows_relevant_region_for_long_doc(self, isolated_storage: Path) -> None:
        documents.create("Test")
        # Long document: head, many filler lines, then the target near the end.
        head = "= Document Title\n"
        filler = "\n".join(f"Filler line {i}" for i in range(50))
        target_line = "The quick brown fox jumps over the lazy dog."
        documents.set_source("test", f"{head}{filler}\n= Final Section\n{target_line}\n")
        result = documents.patch_source(
            "test",
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

    def test_context_includes_line_numbers(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Alpha\n= Beta\n= Gamma\n")
        result = documents.patch_source("test", "= Betaa", "= Beta2")
        assert result.nearest_match is not None
        # Line number gutter present (box-drawing pipe)
        assert "│" in result.nearest_match.context


class TestInputValidation:
    """Programming-error inputs still raise (these aren't LLM contract cases)."""

    def test_empty_find_raises(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Hello")
        with pytest.raises(ValueError, match="non-empty"):
            documents.patch_source("test", "", "x")

    def test_empty_edits_list_raises(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Hello")
        with pytest.raises(ValueError, match="non-empty"):
            documents.patch_source_batch("test", [])

    def test_batch_entry_missing_find_raises(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Hello")
        with pytest.raises(ValueError, match="non-empty"):
            documents.patch_source_batch("test", [{"replace": "x"}])
