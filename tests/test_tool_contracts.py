"""Tool contract tests — verify return shapes match what the UI expects.

These tests are the contract between the Python server and the TypeScript UI.
If a return type changes here, the UI types in ui/src/App.tsx must be updated.

Rewritten for v3: no references to configure_brand, BrandConfig, BrandPresetInfo,
or StarterInfo. Theme is parsed from Typst source, not a brand.json.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
import pytest_asyncio

from mcp_collateral.models import (
    DocumentInfo,
    TemplateInfo,
    WorkspaceState,
)
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

    # Reset template seeding flag so each test gets fresh seeds
    import mcp_collateral.templates as tmod

    monkeypatch.setattr(tmod, "_seeded", False)

    # Create dirs and seed templates
    from mcp_collateral import store

    store._ensure_dirs()
    store.seed_templates()

    return Workspace()


# ---------------------------------------------------------------------------
# Theme contracts
# ---------------------------------------------------------------------------


class TestThemeContracts:
    """get_theme returns dict with colors/fonts/spacing; set_theme returns WorkspaceState."""

    def test_get_theme_returns_dict_with_expected_keys(self, workspace: Workspace) -> None:
        result = workspace.get_theme()
        assert isinstance(result, dict)
        assert "colors" in result
        assert "fonts" in result
        assert "spacing" in result

    def test_get_theme_values_are_dicts(self, workspace: Workspace) -> None:
        result = workspace.get_theme()
        assert isinstance(result["colors"], dict)
        assert isinstance(result["fonts"], dict)
        assert isinstance(result["spacing"], dict)

    def test_set_theme_returns_workspace_state(self, workspace: Workspace) -> None:
        # Create a doc with a template that has a theme block
        workspace.create_document("Test", template_id="one-pager")
        result = workspace.set_theme({"accent": "#ff0000"})
        assert isinstance(result, WorkspaceState)


# ---------------------------------------------------------------------------
# Template contracts
# ---------------------------------------------------------------------------


class TestTemplateContracts:
    """list_templates returns list[TemplateInfo]; create/duplicate/delete work."""

    def test_list_templates_returns_list(self, workspace: Workspace) -> None:
        result = workspace.list_templates()
        assert isinstance(result, list)
        assert len(result) >= 1  # seed templates

    def test_list_templates_items_are_template_info(self, workspace: Workspace) -> None:
        result = workspace.list_templates()
        for t in result:
            assert isinstance(t, TemplateInfo)
            assert isinstance(t.id, str)
            assert isinstance(t.name, str)
            assert isinstance(t.page_count, int)

    def test_create_template_returns_template_info(self, workspace: Workspace) -> None:
        result = workspace.create_template("test-tpl", "Test", "A test", "// source")
        assert isinstance(result, TemplateInfo)
        assert result.id == "test-tpl"
        assert result.name == "Test"

    def test_duplicate_template_returns_template_info(self, workspace: Workspace) -> None:
        templates = workspace.list_templates()
        first_id = templates[0].id
        result = workspace.duplicate_template(first_id, f"{first_id}-copy", "Copy")
        assert isinstance(result, TemplateInfo)
        assert result.id == f"{first_id}-copy"

    def test_delete_template_removes_it(self, workspace: Workspace) -> None:
        workspace.create_template("to-delete", "Delete Me", "desc", "// src")
        workspace.delete_template("to-delete")
        ids = [t.id for t in workspace.list_templates()]
        assert "to-delete" not in ids

    def test_save_as_template_returns_template_info(self, workspace: Workspace) -> None:
        templates = workspace.list_templates()
        if templates:
            workspace.create_document("Test", template_id=templates[0].id)
        else:
            workspace.create_document("Test")
            workspace.set_source("= Real content here")
        result = workspace.save_as_template("My Template", "desc")
        assert isinstance(result, TemplateInfo)


# ---------------------------------------------------------------------------
# Document contracts
# ---------------------------------------------------------------------------


class TestDocumentContracts:
    """Document tools return WorkspaceState or DocumentInfo."""

    def test_create_document_returns_workspace_state(self, workspace: Workspace) -> None:
        result = workspace.create_document("Test Doc")
        assert isinstance(result, WorkspaceState)
        assert result.document_id is not None
        assert result.template_id is None

    def test_create_document_with_template_has_template_id(self, workspace: Workspace) -> None:
        templates = workspace.list_templates()
        if not templates:
            pytest.skip("No seed templates available")
        result = workspace.create_document("Test", template_id=templates[0].id)
        assert isinstance(result, WorkspaceState)
        assert result.template_id == templates[0].id
        assert result.document_id is not None

    def test_list_documents_returns_list_of_document_info(self, workspace: Workspace) -> None:
        result = workspace.list_documents()
        assert isinstance(result, list)
        for d in result:
            assert isinstance(d, DocumentInfo)

    def test_save_document_returns_document_info(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        result = workspace.save_document()
        assert isinstance(result, DocumentInfo)
        assert result.id == "test"

    def test_get_state_returns_workspace_state(self, workspace: Workspace) -> None:
        result = workspace.get_state()
        assert isinstance(result, WorkspaceState)
        assert hasattr(result, "template_id")
        assert hasattr(result, "theme")
        # v3: no starter_id
        assert not hasattr(result, "starter_id")


# ---------------------------------------------------------------------------
# Editing contracts
# ---------------------------------------------------------------------------


class TestEditingContracts:
    """set_source and patch_source return WorkspaceState."""

    def test_set_source_returns_workspace_state(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        result = workspace.set_source("#set text(size: 12pt)\n= Hello")
        assert isinstance(result, WorkspaceState)

    def test_patch_source_returns_workspace_state(self, workspace: Workspace) -> None:
        workspace.create_document("Test")
        workspace.set_source("#set text(size: 12pt)\n= Hello")
        result = workspace.patch_source("Hello", "World")
        assert isinstance(result, WorkspaceState)


# ---------------------------------------------------------------------------
# Asset contracts
# ---------------------------------------------------------------------------


class TestAssetContracts:
    """Asset tools: list_assets -> list[str], upload_asset -> dict."""

    def test_list_assets_returns_list_of_str(self, workspace: Workspace) -> None:
        result = workspace.list_assets()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_upload_asset_returns_dict(self, workspace: Workspace) -> None:
        data = base64.b64encode(b"fake png data").decode()
        result = workspace.upload_asset(data, "test.png")
        assert isinstance(result, dict)
        assert "filename" in result

    def test_upload_then_list_assets(self, workspace: Workspace) -> None:
        data = base64.b64encode(b"fake").decode()
        workspace.upload_asset(data, "logo.png")
        result = workspace.list_assets()
        assert "logo.png" in result

    def test_delete_asset_returns_dict(self, workspace: Workspace) -> None:
        data = base64.b64encode(b"fake").decode()
        workspace.upload_asset(data, "temp.png")
        result = workspace.delete_asset("temp.png")
        assert isinstance(result, dict)
        assert result["status"] == "deleted"

    def test_asset_filename_sanitization(self, workspace: Workspace) -> None:
        data = base64.b64encode(b"fake").decode()
        with pytest.raises(ValueError, match="Invalid"):
            workspace.upload_asset(data, "../etc/passwd")


# ---------------------------------------------------------------------------
# Voice contracts
# ---------------------------------------------------------------------------


class TestVoiceContracts:
    """get_voice -> str, set_voice -> dict."""

    def test_get_voice_returns_str(self, workspace: Workspace) -> None:
        result = workspace.get_voice()
        assert isinstance(result, str)

    def test_set_voice_returns_dict(self, workspace: Workspace) -> None:
        result = workspace.set_voice("Be direct.")
        assert isinstance(result, dict)
        assert "status" in result

    def test_voice_roundtrip(self, workspace: Workspace) -> None:
        workspace.set_voice("Be concise.")
        result = workspace.get_voice()
        assert result == "Be concise."


# ---------------------------------------------------------------------------
# Component contracts
# ---------------------------------------------------------------------------


class TestComponentContracts:
    """get_components -> str, set_components -> dict."""

    def test_get_components_returns_str(self, workspace: Workspace) -> None:
        result = workspace.get_components()
        assert isinstance(result, str)

    def test_set_components_returns_dict(self, workspace: Workspace) -> None:
        result = workspace.set_components("#let foo(x) = x")
        assert isinstance(result, dict)
        assert "status" in result

    def test_components_roundtrip(self, workspace: Workspace) -> None:
        workspace.set_components("#let bar(x) = x")
        result = workspace.get_components()
        assert "#let bar(x) = x" in result


# ---------------------------------------------------------------------------
# Font contracts
# ---------------------------------------------------------------------------


class TestFontContracts:
    """list_fonts -> list[str]."""

    def test_list_fonts_returns_list_of_str(self, workspace: Workspace) -> None:
        result = workspace.list_fonts()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_install_font_returns_dict(self, workspace: Workspace) -> None:
        data = base64.b64encode(b"\x00\x01\x00\x00").decode()
        result = workspace.install_font(base64_data=data, filename="test.ttf")
        assert isinstance(result, dict)
        assert "installed" in result
        assert isinstance(result["installed"], list)


# ---------------------------------------------------------------------------
# Rendering contracts — MCP-spec resource_link tool returns
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def mcp_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Spin up the FastMCP server in-process with isolated storage."""
    monkeypatch.setattr("mcp_collateral.store.BASE_DIR", tmp_path)
    monkeypatch.setattr("mcp_collateral.store.ASSETS_DIR", tmp_path / "assets")
    monkeypatch.setattr("mcp_collateral.store.FONTS_DIR", tmp_path / "fonts")
    monkeypatch.setattr("mcp_collateral.store.TEMPLATES_DIR", tmp_path / "templates")
    monkeypatch.setattr("mcp_collateral.store.DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr("mcp_collateral.store.COMPILE_DIR", tmp_path / "_compile")

    import mcp_collateral.templates as tmod

    monkeypatch.setattr(tmod, "_seeded", False)

    from mcp_collateral import server as server_mod
    from mcp_collateral import store

    store._ensure_dirs()
    store.seed_templates()

    # Replace the module-level workspace so tools use isolated storage.
    monkeypatch.setattr(server_mod, "_ws", Workspace())

    from fastmcp import Client

    async with Client(server_mod.mcp) as client:
        yield client


def _result_byte_size(result) -> int:
    """Estimate on-the-wire size of a CallToolResult's content."""
    total = 0
    for block in result.content:
        # block is a pydantic model; use json dump length as a proxy
        total += len(block.model_dump_json())
    return total


@pytest.mark.asyncio
class TestRenderingContracts:
    """Preview/export tools return small results with resource_link blocks."""

    async def test_preview_returns_pdf_resource_link(self, mcp_client) -> None:
        await mcp_client.call_tool("create_document", {"name": "Preview Doc"})
        result = await mcp_client.call_tool("preview", {})

        assert _result_byte_size(result) < 10_000

        links = [b for b in result.content if getattr(b, "type", None) == "resource_link"]
        assert len(links) == 1
        link = links[0]
        assert str(link.uri).startswith("collateral://exports/")
        assert str(link.uri).endswith(".pdf")
        assert link.mimeType == "application/pdf"

        for b in result.content:
            dumped = b.model_dump_json()
            assert len(dumped) < 2_000, "no block should inline large bytes"

        data = result.structured_content
        assert data is not None
        assert data["mime_type"] == "application/pdf"
        assert data["size_bytes"] > 0
        assert data["export_id"].startswith("exp_")

    async def test_preview_resource_link_fetches_pdf(self, mcp_client) -> None:
        await mcp_client.call_tool("create_document", {"name": "Fetch Doc"})
        result = await mcp_client.call_tool("preview", {})
        link = next(b for b in result.content if getattr(b, "type", None) == "resource_link")

        contents = await mcp_client.read_resource(str(link.uri))
        assert contents, "resources/read must return content"
        import base64 as _b64

        first = contents[0]
        raw = _b64.b64decode(first.blob) if hasattr(first, "blob") else first.text.encode()
        assert raw.startswith(b"%PDF")

    async def test_preview_template_returns_pdf_resource_link(self, mcp_client) -> None:
        templates_result = await mcp_client.call_tool("list_templates", {})
        templates = templates_result.structured_content
        tlist = (
            templates["result"]
            if isinstance(templates, dict) and "result" in templates
            else templates
        )
        if not tlist:
            pytest.skip("No seed templates available")
        tid = tlist[0]["id"]

        result = await mcp_client.call_tool("preview_template", {"template_id": tid})
        assert _result_byte_size(result) < 10_000
        links = [b for b in result.content if getattr(b, "type", None) == "resource_link"]
        assert len(links) == 1
        link = links[0]
        assert str(link.uri).startswith("collateral://exports/")
        assert link.mimeType == "application/pdf"

    async def test_export_pdf_returns_resource_link(self, mcp_client) -> None:
        await mcp_client.call_tool("create_document", {"name": "Export Doc"})
        result = await mcp_client.call_tool("export_pdf", {})

        assert _result_byte_size(result) < 10_000

        links = [b for b in result.content if getattr(b, "type", None) == "resource_link"]
        assert len(links) == 1
        link = links[0]
        assert str(link.uri).startswith("collateral://exports/")
        assert str(link.uri).endswith(".pdf")
        assert link.mimeType == "application/pdf"

        data = result.structured_content
        assert data is not None
        assert data["mime_type"] == "application/pdf"
        assert data["size_bytes"] > 0
        assert data["export_id"].startswith("exp_")

    async def test_export_pdf_resource_link_fetches_pdf(self, mcp_client) -> None:
        await mcp_client.call_tool("create_document", {"name": "Fetch PDF"})
        result = await mcp_client.call_tool("export_pdf", {})
        link = next(b for b in result.content if getattr(b, "type", None) == "resource_link")

        contents = await mcp_client.read_resource(str(link.uri))
        assert contents
        import base64 as _b64

        first = contents[0]
        raw = _b64.b64decode(first.blob) if hasattr(first, "blob") else first.text.encode()
        assert raw.startswith(b"%PDF")

    async def test_compile_typst_returns_resource_link(self, mcp_client) -> None:
        source = '#set page(paper: "us-letter")\n= Hello\nWorld.'
        result = await mcp_client.call_tool("compile_typst", {"source": source})
        assert _result_byte_size(result) < 10_000
        links = [b for b in result.content if getattr(b, "type", None) == "resource_link"]
        assert len(links) == 1
        assert links[0].mimeType == "application/pdf"


class TestExportResourceTemplate:
    """The collateral://exports/{export_id}.{ext} resource template works."""

    def test_store_and_load_export_roundtrip(self, workspace: Workspace, tmp_path: Path) -> None:
        # Unused workspace fixture just isolates store.BASE_DIR.
        del workspace

        from mcp_collateral.workspace import load_export, store_export

        export_id, path = store_export(b"hello bytes", "pdf")
        assert path.exists()
        assert export_id.startswith("exp_")
        assert load_export(export_id, "pdf") == b"hello bytes"

    def test_load_export_missing_returns_none(self, workspace: Workspace) -> None:
        del workspace
        from mcp_collateral.workspace import load_export

        assert load_export("exp_missing", "pdf") is None


# ---------------------------------------------------------------------------
# Auto-save contract
# ---------------------------------------------------------------------------


class TestAutoSaveContract:
    """Edits auto-save and write output.pdf to disk."""

    def test_set_source_writes_output_pdf(self, workspace: Workspace, tmp_path: Path) -> None:
        workspace.create_document("Test")
        workspace.set_source("#set text(size: 12pt)\n= Saved")
        pdf_path = tmp_path / "documents" / "test" / "output.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_patch_source_writes_output_pdf(self, workspace: Workspace, tmp_path: Path) -> None:
        workspace.create_document("Test")
        workspace.set_source("#set text(size: 12pt)\n= Hello")
        workspace.patch_source("Hello", "Patched")
        pdf_path = tmp_path / "documents" / "test" / "output.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_patch_source_auto_saves_source(self, workspace: Workspace, tmp_path: Path) -> None:
        workspace.create_document("Test")
        workspace.set_source("#set text(size: 12pt)\n= Hello")
        workspace.patch_source("Hello", "Saved")
        source_path = tmp_path / "documents" / "test" / "source.typ"
        assert source_path.exists()
        assert "Saved" in source_path.read_text()
