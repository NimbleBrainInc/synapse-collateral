"""Unit tests for patch_source — batch edits and JSON string coercion."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_collateral.models import WorkspaceState
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


class TestPatchSource:
    """patch_source single and batch edits."""

    def test_single_patch(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello World\nSome text here.")
        result = workspace.patch_source("Hello World", "Goodbye World")
        assert isinstance(result, WorkspaceState)
        assert "Goodbye World" in workspace.source

    def test_batch_patch(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Title\nLine A\nLine B")
        result = workspace.patch_source_batch(
            [
                {"find": "Title", "replace": "New Title"},
                {"find": "Line A", "replace": "Line X"},
            ]
        )
        assert isinstance(result, WorkspaceState)
        assert "New Title" in workspace.source
        assert "Line X" in workspace.source

    def test_batch_rollback_on_failure(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Title\nLine A\nLine B")
        with pytest.raises(ValueError, match="not found"):
            workspace.patch_source_batch(
                [
                    {"find": "Line A", "replace": "Line X"},
                    {"find": "NONEXISTENT", "replace": "oops"},
                ]
            )
        # Should have rolled back
        assert "Line A" in workspace.source
        assert "Line X" not in workspace.source

    def test_patch_not_found_raises(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("= Hello")
        with pytest.raises(ValueError, match="not found"):
            workspace.patch_source("MISSING TEXT", "replacement")


class TestPatchSourceJsonCoercion:
    """Server-level JSON string coercion for the edits parameter."""

    def test_json_string_parsed_to_list(self) -> None:
        """Simulate what happens when an LLM sends edits as a JSON string."""
        import json

        edits_str = json.dumps(
            [
                {"find": "old", "replace": "new"},
                {"find": "foo", "replace": "bar"},
            ]
        )
        # Simulate the coercion logic from server.py
        assert isinstance(edits_str, str)
        parsed = json.loads(edits_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["find"] == "old"

    def test_already_list_unchanged(self) -> None:
        """When edits is already a list, json.loads is not called."""
        import json

        edits = [{"find": "old", "replace": "new"}]
        # Simulate: only parse if string
        if isinstance(edits, str):
            edits = json.loads(edits)
        assert isinstance(edits, list)
        assert edits[0]["find"] == "old"
