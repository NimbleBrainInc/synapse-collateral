"""Tests for the stateless documents module.

These tests are the contract for the explicit-document_id model. They lock
in:
  - every read/write takes document_id; nothing operates on an implicit cursor
  - operations against doc A never affect doc B (the bug this refactor fixes)
  - on-disk artifacts (source.typ, output.pdf, meta.json) match expectations
  - mtime-based PDF cache invalidates correctly
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_collateral import documents
from mcp_collateral.models import (
    DocumentInfo,
    DocumentState,
    PatchSourceResult,
    SourceResponse,
)


@pytest.fixture()
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point all storage roots at a tmp_path. Returns the storage root."""
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


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_create_returns_state_with_id(self, isolated_storage: Path) -> None:
        state = documents.create("First Doc")
        assert isinstance(state, DocumentState)
        assert state.document_id == "first-doc"
        assert state.document_name == "First Doc"
        assert state.template_id is None

    def test_create_collision_yields_unique_slug(self, isolated_storage: Path) -> None:
        a = documents.create("My Doc")
        b = documents.create("My Doc")
        assert a.document_id == "my-doc"
        assert b.document_id == "my-doc-2"

    def test_get_reads_from_disk(self, isolated_storage: Path) -> None:
        documents.create("Persisted")
        # Re-fetch via get — proves we're reading disk, not memory.
        state = documents.get("persisted")
        assert state.document_name == "Persisted"

    def test_list_all_returns_document_info(self, isolated_storage: Path) -> None:
        documents.create("Doc One")
        documents.create("Doc Two")
        all_docs = documents.list_all()
        ids = sorted(d.id for d in all_docs)
        assert ids == ["doc-one", "doc-two"]
        for d in all_docs:
            assert isinstance(d, DocumentInfo)

    def test_save_renames(self, isolated_storage: Path) -> None:
        documents.create("Old Name")
        info = documents.save("old-name", name="New Name")
        assert info.name == "New Name"
        assert documents.get("old-name").document_name == "New Name"

    def test_delete_removes_from_disk(self, isolated_storage: Path) -> None:
        documents.create("Doomed")
        documents.delete("doomed")
        assert documents.list_all() == []
        with pytest.raises(FileNotFoundError):
            documents.get("doomed")


# ---------------------------------------------------------------------------
# Source read/write
# ---------------------------------------------------------------------------


class TestSource:
    def test_get_source_returns_object_with_id(self, isolated_storage: Path) -> None:
        documents.create("Test")
        result = documents.get_source("test")
        assert isinstance(result, SourceResponse)
        assert result.document_id == "test"
        # New documents are seeded with BLANK_SOURCE
        assert "Untitled Document" in result.source

    def test_set_source_persists_and_compiles(self, isolated_storage: Path) -> None:
        documents.create("Test")
        state = documents.set_source("test", "= Hello World\n")
        assert isinstance(state, DocumentState)
        # source.typ written
        src_path = isolated_storage / "documents" / "test" / "source.typ"
        assert src_path.read_text() == "= Hello World\n"
        # output.pdf written by compile
        pdf_path = isolated_storage / "documents" / "test" / "output.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_set_source_failure_leaves_disk_untouched(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "= Valid")
        original_pdf = (isolated_storage / "documents" / "test" / "output.pdf").read_bytes()
        with pytest.raises(RuntimeError, match="Typst compilation failed"):
            documents.set_source("test", "#let broken =")
        # Source on disk is the previous valid version
        src = (isolated_storage / "documents" / "test" / "source.typ").read_text()
        assert src == "= Valid"
        # PDF on disk is the previous valid version
        assert (isolated_storage / "documents" / "test" / "output.pdf").read_bytes() == original_pdf


# ---------------------------------------------------------------------------
# Patch source
# ---------------------------------------------------------------------------


class TestPatch:
    def test_patch_applies_and_compiles(self, isolated_storage: Path) -> None:
        documents.create("T")
        documents.set_source("t", "= Hello\nText.")
        result = documents.patch_source("t", "Hello", "Goodbye")
        assert isinstance(result, PatchSourceResult)
        assert result.applied is True
        assert result.compiled is True
        assert result.document is not None
        src = (isolated_storage / "documents" / "t" / "source.typ").read_text()
        assert "Goodbye" in src

    def test_patch_text_not_found_does_not_touch_disk(self, isolated_storage: Path) -> None:
        documents.create("T")
        documents.set_source("t", "= Hello\nText.")
        before = (isolated_storage / "documents" / "t" / "source.typ").read_text()
        result = documents.patch_source("t", "Nonexistent", "x")
        assert result.applied is False
        assert result.reason == "text_not_found"
        after = (isolated_storage / "documents" / "t" / "source.typ").read_text()
        assert after == before

    def test_patch_compile_error_does_not_touch_disk(self, isolated_storage: Path) -> None:
        documents.create("T")
        documents.set_source("t", "= Hello\nBody.")
        before_src = (isolated_storage / "documents" / "t" / "source.typ").read_text()
        before_pdf = (isolated_storage / "documents" / "t" / "output.pdf").read_bytes()
        result = documents.patch_source("t", "= Hello", "#let broken =")
        assert result.applied is False
        assert result.reason == "compile_error"
        # Both source and PDF unchanged
        assert (isolated_storage / "documents" / "t" / "source.typ").read_text() == before_src
        assert (isolated_storage / "documents" / "t" / "output.pdf").read_bytes() == before_pdf

    def test_patch_batch_sequential(self, isolated_storage: Path) -> None:
        documents.create("T")
        documents.set_source("t", "= Title\nLine A\nLine B")
        result = documents.patch_source_batch(
            "t",
            [
                {"find": "Title", "replace": "New Title"},
                {"find": "Line A", "replace": "Line X"},
            ],
        )
        assert result.applied is True
        src = (isolated_storage / "documents" / "t" / "source.typ").read_text()
        assert "New Title" in src and "Line X" in src

    def test_patch_validate_false_writes_source_invalidates_pdf(
        self, isolated_storage: Path
    ) -> None:
        """Staging without compile must invalidate the cache explicitly so
        the next render recompiles, regardless of mtime resolution."""
        documents.create("T")
        documents.set_source("t", "= Hello\nText.")
        pdf_path = isolated_storage / "documents" / "t" / "output.pdf"
        assert pdf_path.exists()
        result = documents.patch_source("t", "Hello", "Stage Without Compile", validate=False)
        assert result.applied is True
        assert result.compiled is False
        # Source updated; cached PDF deleted so the next render recompiles.
        assert (
            "Stage Without Compile"
            in (isolated_storage / "documents" / "t" / "source.typ").read_text()
        )
        assert not pdf_path.exists()
        # Render after staging recompiles cleanly and rewrites output.pdf.
        documents.render_pdf("t")
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# source_sha — per-edit fingerprint that keeps the host loop supervisor
# from disabling the edit tool after 3 successive identical envelopes
# ---------------------------------------------------------------------------


class TestSourceSha:
    def test_successive_edits_emit_distinct_source_sha(self, isolated_storage: Path) -> None:
        """Each successful edit must change the returned source_sha.

        Regression for the loop-supervisor trip: the host fingerprints tool
        results and disables a tool that returns the *same* result 3x in a
        row. Without source_sha, every applied edit returned a byte-identical
        success envelope (applied/compiled + an unchanged document snapshot),
        so a normal batch-patch workflow tripped the supervisor and lost
        write access mid-document. The per-edit source_sha makes consecutive
        successful edits distinct.
        """
        documents.create("Test")
        documents.set_source("test", "= A\n= B\n= C\n")
        r1 = documents.patch_source("test", "= A", "= A1")
        r2 = documents.patch_source("test", "= B", "= B1")
        r3 = documents.patch_source("test", "= C", "= C1")
        shas = [r.document.source_sha for r in (r1, r2, r3)]
        assert all(s is not None for s in shas)
        # All three distinct → no two consecutive results are byte-identical.
        assert len(set(shas)) == 3

    def test_source_sha_reaches_fastmcp_content_text(self, isolated_storage: Path) -> None:
        """The supervisor fingerprints the result's *content text*, not the
        Python object. This bug only stays fixed if source_sha survives
        FastMCP's serialization into that text block. Prove it at the
        serialization boundary using FastMCP's own serializer — the same
        function FastMCP uses to build the TextContent for a structured
        return — so a future refactor that returns a hand-built result with
        constant content (reintroducing the bug) fails here.
        """
        from fastmcp.tools.tool import default_serializer

        documents.create("Test")
        documents.set_source("test", "= A\n= B\n")
        r1 = documents.patch_source("test", "= A", "= A1")
        r2 = documents.patch_source("test", "= B", "= B1")
        t1, t2 = default_serializer(r1), default_serializer(r2)
        assert "source_sha" in t1
        # The serialized content text — what the host hashes — differs per edit.
        assert t1 != t2

    def test_source_sha_is_stable_on_no_op_edit(self, isolated_storage: Path) -> None:
        """A no-op edit (find == replace) leaves source_sha unchanged.

        source_sha is a content hash, not a monotonic counter: a genuine
        no-op produces the identical fingerprint, preserving the supervisor's
        ability to catch a tool stuck re-applying the same edit. A counter
        would mask that loop.
        """
        documents.create("Test")
        before = documents.set_source("test", "= Heading\nbody\n").source_sha
        result = documents.patch_source("test", "= Heading", "= Heading")  # no-op
        assert result.applied is True
        assert result.document is not None
        assert result.document.source_sha == before


# ---------------------------------------------------------------------------
# Isolation — the load-bearing test for the bug we're fixing
# ---------------------------------------------------------------------------


class TestIsolation:
    """The whole point of this refactor: tools targeting doc A never
    accidentally write to doc B."""

    def test_set_source_on_a_does_not_change_b(self, isolated_storage: Path) -> None:
        documents.create("Doc A")
        documents.create("Doc B")
        documents.set_source("doc-a", "= I am A\n")
        documents.set_source("doc-b", "= I am B\n")
        assert "I am A" in documents.get_source("doc-a").source
        assert "I am B" in documents.get_source("doc-b").source

    def test_patch_on_a_does_not_change_b(self, isolated_storage: Path) -> None:
        documents.create("A")
        documents.create("B")
        documents.set_source("a", "= Apples\n")
        documents.set_source("b", "= Bananas\n")
        documents.patch_source("a", "Apples", "Avocados")
        # B is untouched
        assert "Bananas" in documents.get_source("b").source
        assert "Avocados" not in documents.get_source("b").source

    def test_interleaved_edits_target_correct_documents(self, isolated_storage: Path) -> None:
        """Mirrors the production incident: agent appears to be working on
        Nuve while the cursor has drifted to IPinfo. With explicit IDs,
        interleaving is safe by construction."""
        documents.create("Nuve")
        documents.create("IPinfo")
        documents.create("Skyfire")
        documents.set_source("nuve", "= Nuve content\n")
        documents.set_source("ipinfo", "= IPinfo content\n")
        documents.set_source("skyfire", "= Skyfire content\n")
        # Now interleave updates in non-obvious order
        documents.patch_source("nuve", "Nuve content", "Nuve v2")
        documents.patch_source("skyfire", "Skyfire content", "Skyfire v2")
        documents.patch_source("ipinfo", "IPinfo content", "IPinfo v2")
        assert "Nuve v2" in documents.get_source("nuve").source
        assert "IPinfo v2" in documents.get_source("ipinfo").source
        assert "Skyfire v2" in documents.get_source("skyfire").source


# ---------------------------------------------------------------------------
# Render / cache
# ---------------------------------------------------------------------------


class TestRender:
    def test_render_pdf_returns_bytes(self, isolated_storage: Path) -> None:
        documents.create("T")
        documents.set_source("t", "= Render Me\n")
        pdf = documents.render_pdf("t")
        assert pdf.startswith(b"%PDF")

    def test_render_uses_disk_cache_when_fresh(self, isolated_storage: Path) -> None:
        documents.create("T")
        documents.set_source("t", "= Cached\n")
        # First render reads from disk cache (output.pdf written by set_source)
        pdf_path = isolated_storage / "documents" / "t" / "output.pdf"
        original_mtime = pdf_path.stat().st_mtime
        documents.render_pdf("t")
        assert pdf_path.stat().st_mtime == original_mtime  # cache hit, no rewrite

    def test_render_recompiles_when_source_newer_than_pdf(self, isolated_storage: Path) -> None:
        """When source.typ is newer than output.pdf (e.g. after a
        validate=False patch), render_pdf must recompile and refresh the
        cache rather than serve the stale PDF."""
        import os

        documents.create("T")
        documents.set_source("t", "= V1\n")
        pdf_path = isolated_storage / "documents" / "t" / "output.pdf"
        src_path = isolated_storage / "documents" / "t" / "source.typ"
        pdf_mtime_before = pdf_path.stat().st_mtime
        # Bump source mtime above the PDF's mtime so the cache check
        # correctly detects staleness.
        new_src_mtime = pdf_mtime_before + 5
        os.utime(src_path, (new_src_mtime, new_src_mtime))
        documents.render_pdf("t")
        # Cache was invalidated → output.pdf was rewritten → mtime advanced
        assert pdf_path.stat().st_mtime > pdf_mtime_before


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


class TestTheme:
    def test_set_theme_updates_source(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        has_theme = next((t for t in tmod.list_templates() if t.id == "one-pager"), None)
        if has_theme is None:
            pytest.skip("one-pager template not seeded")
        documents.create("Themed", template_id="one-pager")
        result = documents.set_theme("themed", {"accent": "#ff0000"})
        assert isinstance(result, DocumentState)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_empty_find_raises(self, isolated_storage: Path) -> None:
        documents.create("T")
        with pytest.raises(ValueError, match="non-empty"):
            documents.patch_source("t", "", "x")

    def test_empty_edits_raises(self, isolated_storage: Path) -> None:
        documents.create("T")
        with pytest.raises(ValueError, match="non-empty"):
            documents.patch_source_batch("t", [])

    def test_get_unknown_document_raises(self, isolated_storage: Path) -> None:
        with pytest.raises(FileNotFoundError):
            documents.get("nonexistent")


class TestStatelessness:
    """Lock in the contract that documents.py holds NO module-level
    mutable state. The original bug was a singleton ``Workspace`` with a
    document_id cursor; if anyone reintroduces a per-process cache or
    cursor as an "optimization", this test fires.
    """

    def test_no_module_level_mutable_state(self) -> None:
        # Allowed module-level names: callables, classes, modules, the
        # ``__future__.annotations`` sentinel, immutable constants (str,
        # int, frozenset, tuple, compiled regex), and dunder attributes.
        # Anything else suggests mutable per-process state has snuck back in.
        import __future__

        import inspect
        import re as re_mod
        from types import ModuleType

        allowed_immutable = (str, int, float, bool, tuple, frozenset, type(None))

        for name, value in vars(documents).items():
            if name.startswith("__"):
                continue
            if (
                callable(value)
                or inspect.isclass(value)
                or isinstance(value, ModuleType)
                or isinstance(value, __future__._Feature)
            ):
                continue
            if isinstance(value, allowed_immutable):
                continue
            if isinstance(value, re_mod.Pattern):
                continue
            raise AssertionError(
                f"documents.{name} is a mutable module-level object "
                f"({type(value).__name__}). The whole point of this module "
                "is statelessness — store mutable state on disk, not in "
                "the module namespace."
            )


class TestDocumentIdValidation:
    """Path-traversal defense: every doc tool takes document_id from the
    LLM/UI now, so the store must reject anything that isn't a slug."""

    @pytest.mark.parametrize(
        "bad_id",
        [
            "../etc/passwd",
            "..",
            "foo/bar",
            "foo\\bar",
            "foo.bar",  # dots disallowed — slugs are URL-shaped
            "Foo",  # uppercase disallowed
            "-leading-hyphen",
            "trailing-hyphen-",
            "",
            " ",
            "foo bar",
        ],
    )
    def test_set_source_rejects_unsafe_document_id(
        self, isolated_storage: Path, bad_id: str
    ) -> None:
        with pytest.raises(ValueError, match="Invalid document_id"):
            documents.set_source(bad_id, "= Hello")

    @pytest.mark.parametrize(
        "bad_id",
        ["../escape", "foo/bar", ".."],
    )
    def test_get_rejects_unsafe_document_id(self, isolated_storage: Path, bad_id: str) -> None:
        with pytest.raises(ValueError, match="Invalid document_id"):
            documents.get(bad_id)

    def test_delete_rejects_unsafe_document_id(self, isolated_storage: Path) -> None:
        with pytest.raises(ValueError, match="Invalid document_id"):
            documents.delete("..")

    def test_render_rejects_unsafe_document_id(self, isolated_storage: Path) -> None:
        with pytest.raises(ValueError, match="Invalid document_id"):
            documents.render_pdf("../foo")

    def test_valid_slug_accepted(self, isolated_storage: Path) -> None:
        # Sanity: legitimate slugs pass.
        documents.create("Hello World")
        documents.set_source("hello-world", "= Hi")
        assert "Hi" in documents.get_source("hello-world").source
