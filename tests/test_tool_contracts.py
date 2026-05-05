"""Tool contract tests — verify return shapes match what the UI expects.

These tests are the contract between the Python server and the TypeScript
UI. If a return type changes here, the UI types in ``ui/src/types.ts``
must be updated.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
import pytest_asyncio

from mcp_collateral import documents, workspace
from mcp_collateral.models import (
    DocumentInfo,
    DocumentState,
    PatchSourceResult,
    TemplateInfo,
)

# 1x1 PNG bytes for upload_asset contract tests (upload_asset validates).
_VALID_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)
_VALID_PNG_B64 = base64.b64encode(_VALID_PNG).decode()


@pytest.fixture()
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point all storage roots at tmp_path. Returns the storage root."""
    monkeypatch.setattr("mcp_collateral.store.BASE_DIR", tmp_path)
    monkeypatch.setattr("mcp_collateral.store.ASSETS_DIR", tmp_path / "assets")
    monkeypatch.setattr("mcp_collateral.store.FONTS_DIR", tmp_path / "fonts")
    monkeypatch.setattr("mcp_collateral.store.TEMPLATES_DIR", tmp_path / "templates")
    monkeypatch.setattr("mcp_collateral.store.DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr("mcp_collateral.store.COMPILE_DIR", tmp_path / "_compile")

    # Reset template seeding flag so each test gets fresh seeds
    import mcp_collateral.templates as tmod

    monkeypatch.setattr(tmod, "_seeded", False)

    from mcp_collateral import store

    store._ensure_dirs()
    store.seed_templates()
    return tmp_path


# ---------------------------------------------------------------------------
# Theme contracts
# ---------------------------------------------------------------------------


class TestThemeContracts:
    """get_theme returns dict with colors/fonts/spacing; set_theme returns DocumentState."""

    def test_get_theme_returns_dict_with_expected_keys(self, isolated_storage: Path) -> None:
        documents.create("Test")
        result = documents.get_theme("test")
        assert isinstance(result, dict)
        assert "colors" in result
        assert "fonts" in result
        assert "spacing" in result

    def test_get_theme_values_are_dicts(self, isolated_storage: Path) -> None:
        documents.create("Test")
        result = documents.get_theme("test")
        assert isinstance(result["colors"], dict)
        assert isinstance(result["fonts"], dict)
        assert isinstance(result["spacing"], dict)

    def test_set_theme_returns_document_state(self, isolated_storage: Path) -> None:
        # Create a doc with a template that has a theme block
        documents.create("Test", template_id="one-pager")
        result = documents.set_theme("test", {"accent": "#ff0000"})
        assert isinstance(result, DocumentState)


# ---------------------------------------------------------------------------
# Template contracts
# ---------------------------------------------------------------------------


class TestTemplateContracts:
    """list_templates returns list[TemplateInfo]; create/duplicate/delete work."""

    def test_list_templates_returns_list(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        result = tmod.list_templates()
        assert isinstance(result, list)
        assert len(result) >= 1  # seed templates

    def test_list_templates_items_are_template_info(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        result = tmod.list_templates()
        for t in result:
            assert isinstance(t, TemplateInfo)
            assert isinstance(t.id, str)
            assert isinstance(t.name, str)
            assert isinstance(t.page_count, int)

    def test_create_template_returns_template_info(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        result = tmod.create_template("test-tpl", "Test", "// source", "A test")
        assert isinstance(result, TemplateInfo)
        assert result.id == "test-tpl"
        assert result.name == "Test"

    def test_duplicate_template_returns_template_info(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        templates_list = tmod.list_templates()
        first_id = templates_list[0].id
        result = tmod.duplicate_template(first_id, f"{first_id}-copy", "Copy")
        assert isinstance(result, TemplateInfo)
        assert result.id == f"{first_id}-copy"

    def test_delete_template_removes_it(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        tmod.create_template("to-delete", "Delete Me", "// src", "desc")
        tmod.delete_template("to-delete")
        ids = [t.id for t in tmod.list_templates()]
        assert "to-delete" not in ids

    def test_save_as_template_returns_template_info(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        templates_list = tmod.list_templates()
        if templates_list:
            documents.create("Test", template_id=templates_list[0].id)
        else:
            documents.create("Test")
            documents.set_source("test", "= Real content here")
        result = documents.save_as_template("test", "My Template", "desc")
        assert isinstance(result, TemplateInfo)


# ---------------------------------------------------------------------------
# Document contracts
# ---------------------------------------------------------------------------


class TestDocumentContracts:
    """Document tools return DocumentState or DocumentInfo."""

    def test_create_document_returns_document_state(self, isolated_storage: Path) -> None:
        result = documents.create("Test Doc")
        assert isinstance(result, DocumentState)
        assert result.document_id is not None
        assert result.template_id is None

    def test_create_document_with_template_has_template_id(self, isolated_storage: Path) -> None:
        from mcp_collateral import templates as tmod

        templates_list = tmod.list_templates()
        if not templates_list:
            pytest.skip("No seed templates available")
        result = documents.create("Test", template_id=templates_list[0].id)
        assert isinstance(result, DocumentState)
        assert result.template_id == templates_list[0].id
        assert result.document_id is not None

    def test_list_documents_returns_list_of_document_info(self, isolated_storage: Path) -> None:
        result = documents.list_all()
        assert isinstance(result, list)
        for d in result:
            assert isinstance(d, DocumentInfo)

    def test_save_document_returns_document_info(self, isolated_storage: Path) -> None:
        documents.create("Test")
        result = documents.save("test")
        assert isinstance(result, DocumentInfo)
        assert result.id == "test"

    def test_get_document_returns_document_state(self, isolated_storage: Path) -> None:
        documents.create("Test")
        result = documents.get("test")
        assert isinstance(result, DocumentState)
        assert hasattr(result, "template_id")
        assert hasattr(result, "theme")


# ---------------------------------------------------------------------------
# Editing contracts
# ---------------------------------------------------------------------------


class TestEditingContracts:
    """set_source returns DocumentState; patch_source returns PatchSourceResult."""

    def test_set_source_returns_document_state(self, isolated_storage: Path) -> None:
        documents.create("Test")
        result = documents.set_source("test", "#set text(size: 12pt)\n= Hello")
        assert isinstance(result, DocumentState)

    def test_patch_source_returns_patch_result(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "#set text(size: 12pt)\n= Hello")
        result = documents.patch_source("test", "Hello", "World")
        assert isinstance(result, PatchSourceResult)
        assert result.applied is True
        assert result.compiled is True
        assert result.document is not None


# ---------------------------------------------------------------------------
# Asset contracts
# ---------------------------------------------------------------------------


class TestAssetContracts:
    """Asset tools: list_assets -> list[str], upload_asset -> dict."""

    def test_list_assets_returns_list_of_str(self, isolated_storage: Path) -> None:
        result = workspace.list_assets()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_upload_asset_returns_dict(self, isolated_storage: Path) -> None:
        result = workspace.upload_asset(_VALID_PNG_B64, "test.png")
        assert isinstance(result, dict)
        assert "filename" in result

    def test_upload_then_list_assets(self, isolated_storage: Path) -> None:
        workspace.upload_asset(_VALID_PNG_B64, "logo.png")
        result = workspace.list_assets()
        assert "logo.png" in result

    def test_delete_asset_returns_dict(self, isolated_storage: Path) -> None:
        workspace.upload_asset(_VALID_PNG_B64, "temp.png")
        result = workspace.delete_asset("temp.png")
        assert isinstance(result, dict)
        assert result["status"] == "deleted"

    def test_asset_filename_sanitization(self, isolated_storage: Path) -> None:
        # Bytes are valid; filename traversal is what's being tested.
        with pytest.raises(ValueError, match="Invalid"):
            workspace.upload_asset(_VALID_PNG_B64, "../etc/passwd")


# ---------------------------------------------------------------------------
# Voice contracts
# ---------------------------------------------------------------------------


class TestVoiceContracts:
    """get_voice -> str, set_voice -> dict."""

    def test_get_voice_returns_str(self, isolated_storage: Path) -> None:
        result = workspace.get_voice()
        assert isinstance(result, str)

    def test_set_voice_returns_dict(self, isolated_storage: Path) -> None:
        result = workspace.set_voice("Be direct.")
        assert isinstance(result, dict)
        assert "status" in result

    def test_voice_roundtrip(self, isolated_storage: Path) -> None:
        workspace.set_voice("Be concise.")
        result = workspace.get_voice()
        assert result == "Be concise."


# ---------------------------------------------------------------------------
# Component contracts
# ---------------------------------------------------------------------------


class TestComponentContracts:
    """get_components -> str, set_components -> dict."""

    def test_get_components_returns_str(self, isolated_storage: Path) -> None:
        result = workspace.get_components()
        assert isinstance(result, str)

    def test_set_components_returns_dict(self, isolated_storage: Path) -> None:
        result = workspace.set_components("#let foo(x) = x")
        assert isinstance(result, dict)
        assert "status" in result

    def test_components_roundtrip(self, isolated_storage: Path) -> None:
        workspace.set_components("#let bar(x) = x")
        result = workspace.get_components()
        assert "#let bar(x) = x" in result


# ---------------------------------------------------------------------------
# Font contracts
# ---------------------------------------------------------------------------


class TestFontContracts:
    """list_fonts -> list[str]."""

    def test_list_fonts_returns_list_of_str(self, isolated_storage: Path) -> None:
        result = workspace.list_fonts()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_install_font_returns_dict(self, isolated_storage: Path) -> None:
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


def _doc_id_from_create(result) -> str:
    """Extract document_id from a create_document tool result."""
    data = result.structured_content
    return data["document_id"] if isinstance(data, dict) else data.document_id


@pytest.mark.asyncio
class TestRenderingContracts:
    """Preview/export tools return small results with resource_link blocks."""

    async def test_preview_returns_pdf_resource_link(self, mcp_client) -> None:
        create_result = await mcp_client.call_tool("create_document", {"name": "Preview Doc"})
        doc_id = _doc_id_from_create(create_result)
        result = await mcp_client.call_tool("preview", {"document_id": doc_id})

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
        create_result = await mcp_client.call_tool("create_document", {"name": "Fetch Doc"})
        doc_id = _doc_id_from_create(create_result)
        result = await mcp_client.call_tool("preview", {"document_id": doc_id})
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
        create_result = await mcp_client.call_tool("create_document", {"name": "Export Doc"})
        doc_id = _doc_id_from_create(create_result)
        result = await mcp_client.call_tool("export_pdf", {"document_id": doc_id})

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
        create_result = await mcp_client.call_tool("create_document", {"name": "Fetch PDF"})
        doc_id = _doc_id_from_create(create_result)
        result = await mcp_client.call_tool("export_pdf", {"document_id": doc_id})
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

    async def test_patch_source_batch_through_mcp_client(self, mcp_client) -> None:
        """End-to-end: batch edits applied through the MCP server return
        the correct PatchSourceResult shape."""
        create_result = await mcp_client.call_tool("create_document", {"name": "Batch Doc"})
        doc_id = _doc_id_from_create(create_result)
        await mcp_client.call_tool(
            "set_source",
            {"document_id": doc_id, "source": "= Alpha\nBeta\n"},
        )
        result = await mcp_client.call_tool(
            "patch_source",
            {
                "document_id": doc_id,
                "edits": [
                    {"find": "Alpha", "replace": "Apple"},
                    {"find": "Beta", "replace": "Banana"},
                ],
            },
        )
        data = result.structured_content
        assert data is not None
        assert data["applied"] is True
        assert data["compiled"] is True


class TestExportResourceTemplate:
    """The collateral://exports/{export_id}.{ext} resource template works."""

    def test_store_and_load_export_roundtrip(self, isolated_storage: Path) -> None:
        from mcp_collateral.workspace import load_export, store_export

        export_id, path = store_export(b"hello bytes", "pdf")
        assert path.exists()
        assert export_id.startswith("exp_")
        assert load_export(export_id, "pdf") == b"hello bytes"

    def test_load_export_missing_returns_none(self, isolated_storage: Path) -> None:
        from mcp_collateral.workspace import load_export

        assert load_export("exp_missing", "pdf") is None


class TestAssetResourceTemplate:
    """The collateral://assets/{filename} resource template works."""

    def test_asset_resource_returns_bytes_and_mime(self, isolated_storage: Path) -> None:
        from mcp_collateral import server, store

        store.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        (store.ASSETS_DIR / "headshot.png").write_bytes(b"\x89PNG\r\n\x1a\nfakebytes")

        result = server.collateral_asset("headshot.png")
        assert len(result.contents) == 1
        content = result.contents[0]
        assert content.mime_type == "image/png"
        assert content.content.startswith(b"\x89PNG")

    def test_asset_resource_mime_per_extension(self, isolated_storage: Path) -> None:
        from mcp_collateral import server, store

        store.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        cases = {
            "brand.jpg": "image/jpeg",
            "logo.svg": "image/svg+xml",
            "notes.md": "text/markdown",
            "random.bin": "application/octet-stream",
        }
        for filename, expected_mime in cases.items():
            (store.ASSETS_DIR / filename).write_bytes(b"payload")
            result = server.collateral_asset(filename)
            assert result.contents[0].mime_type == expected_mime, filename

    def test_asset_resource_missing_returns_empty(self, isolated_storage: Path) -> None:
        from mcp_collateral import server

        result = server.collateral_asset("does-not-exist.png")
        assert len(result.contents) == 1
        assert result.contents[0].content == b""

    def test_asset_resource_refuses_directory(self, isolated_storage: Path) -> None:
        from mcp_collateral import server, store

        store.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        (store.ASSETS_DIR / "a-folder").mkdir(exist_ok=True)

        result = server.collateral_asset("a-folder")
        assert result.contents[0].content == b""

    def test_asset_resource_rejects_path_traversal(self, isolated_storage: Path) -> None:
        from mcp_collateral import server

        # Classic dot-dot escape
        assert server.collateral_asset("../../../etc/passwd").contents[0].content == b""
        # Nested dot-dot mid-path
        assert server.collateral_asset("sub/../../etc/passwd").contents[0].content == b""
        # Absolute path
        assert server.collateral_asset("/etc/passwd").contents[0].content == b""


# ---------------------------------------------------------------------------
# Auto-save contract
# ---------------------------------------------------------------------------


class TestAutoSaveContract:
    """Edits auto-save and write output.pdf to disk."""

    def test_set_source_writes_output_pdf(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "#set text(size: 12pt)\n= Saved")
        pdf_path = isolated_storage / "documents" / "test" / "output.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_patch_source_writes_output_pdf(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "#set text(size: 12pt)\n= Hello")
        documents.patch_source("test", "Hello", "Patched")
        pdf_path = isolated_storage / "documents" / "test" / "output.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_patch_source_auto_saves_source(self, isolated_storage: Path) -> None:
        documents.create("Test")
        documents.set_source("test", "#set text(size: 12pt)\n= Hello")
        documents.patch_source("test", "Hello", "Saved")
        source_path = isolated_storage / "documents" / "test" / "source.typ"
        assert source_path.exists()
        assert "Saved" in source_path.read_text()


# ---------------------------------------------------------------------------
# Voice tool wrapper — the @mcp.tool catches the cap ValueError and returns a
# structured {"status": "error"} envelope the settings UI consumes. Exercised
# through the MCP client (not Workspace.set_voice, which raises) because an
# over-cap body is reachable only via an agent tool call — the UI disables
# Save above the cap.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestVoiceToolWrapper:
    async def test_set_voice_over_cap_returns_structured_error(self, mcp_client) -> None:
        from mcp_collateral.workspace import MAX_VOICE_BYTES

        oversized = "x" * (MAX_VOICE_BYTES + 1)
        result = await mcp_client.call_tool("set_voice", {"content": oversized})
        # The tool must translate the cap breach into a structured error,
        # NOT let the ValueError cross the wire as a transport-level failure.
        assert result.data["status"] == "error"
        assert "byte limit" in result.data["error"]

    async def test_set_voice_within_cap_saves(self, mcp_client) -> None:
        result = await mcp_client.call_tool("set_voice", {"content": "Be terse."})
        assert result.data["status"] == "saved"

    async def test_app_instructions_resource_round_trips(self, mcp_client) -> None:
        # The platform reads `app://instructions` on every prompt assembly.
        # Unset → empty body (platform omits the overlay).
        empty = await mcp_client.read_resource("app://instructions")
        assert empty[0].text == ""
        # After set_voice the resource serves the saved body verbatim.
        await mcp_client.call_tool("set_voice", {"content": "# Voice\n\nWrite plainly."})
        saved = await mcp_client.read_resource("app://instructions")
        assert saved[0].text == "# Voice\n\nWrite plainly."
