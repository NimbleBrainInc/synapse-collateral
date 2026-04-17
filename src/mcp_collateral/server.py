"""Collateral Studio — Fat MCP server with 30 tools.

Documents are the primary entity. Templates are optional scaffolds.
The agent edits Typst source directly. Documents persist to
~/.collateral/documents/.
"""

from __future__ import annotations

import json
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.resources import ResourceContent, ResourceResult
from fastmcp.tools import ToolResult
from mcp.types import Annotations, ResourceLink, TextContent
from pydantic import AnyUrl

from . import store, templates as template_mod
from .models import (
    DocumentInfo,
    TemplateInfo,
    WorkspaceState,
)
from .workspace import Workspace, load_export, store_export

_EXT_MIME: dict[str, str] = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "txt": "text/plain",
    "md": "text/markdown",
    "json": "application/json",
}


def _mime_for(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_MIME.get(ext, "application/octet-stream")

_USER_ONLY = Annotations(audience=["user"])

_PROJECT_ROOT = Path(str(files("mcp_collateral"))).parent.parent
_UI_HTML = _PROJECT_ROOT / "ui" / "dist" / "index.html"

SKILL_CONTENT = files("mcp_collateral").joinpath("SKILL.md").read_text()
REFERENCE_CONTENT = files("mcp_collateral").joinpath("REFERENCE.md").read_text()

mcp = FastMCP(
    "Collateral Studio",
    instructions=(
        "RULES — follow strictly:\n"
        "1. EDITING: Use patch_source for ALL edits after initial document creation. "
        "Use patch_source(edits=[...]) to batch multiple fixes in one call. "
        "NEVER use set_source to revise an existing document — it wastes tokens "
        "and risks breaking unrelated content.\n"
        "2. set_source is ONLY for writing the initial document from scratch or imported content.\n"
        "3. set_source, patch_source, and set_theme auto-compile. "
        "If the tool succeeds, the edit is valid. Do NOT call preview() to verify.\n"
        "4. Only call preview() when the user asks to SEE the document.\n"
        "5. If any tool fails with a compilation error, diagnose and fix it "
        "before responding. Never report success on failure.\n"
        "6. Use theme tokens (primary, ink, font-display, section-gap) — "
        "never hardcode rgb(), font names, or pt values in the document body.\n"
        "7. Read skill://collateral/usage for tool selection and error recovery."
    ),
)

_ws = Workspace()


# --- Resources ---


@mcp.resource("skill://collateral/usage")
def collateral_skill() -> str:
    """How to effectively use the Collateral Studio tools."""
    content = SKILL_CONTENT
    voice = _ws.get_voice()
    if voice:
        content = content.replace(
            "<!-- VOICE -->",
            f"## Brand Voice\n\n{voice}\n",
        )
    else:
        content = content.replace("<!-- VOICE -->\n\n", "")
    return content


@mcp.resource("skill://collateral/reference")
def collateral_reference() -> str:
    """Detailed tool catalog, error recovery, and anti-patterns."""
    return REFERENCE_CONTENT


@mcp.resource("ui://collateral/main")
def collateral_ui() -> str:
    """The Collateral Studio app UI — rendered in the platform sidebar."""
    if _UI_HTML.exists():
        return _UI_HTML.read_text()
    return "<html><body><p>UI not built. Run <code>cd ui && npm run build</code>.</p></body></html>"


_SETTINGS_HTML = _PROJECT_ROOT / "ui" / "settings.html"


@mcp.resource("ui://collateral/settings")
def collateral_settings_ui() -> str:
    """Collateral configuration panel — brand, voice, assets."""
    if _SETTINGS_HTML.exists():
        return _SETTINGS_HTML.read_text()
    return _INLINE_SETTINGS_HTML  # defined at end of file to keep tools readable


@mcp.resource("ui://collateral/preview.pdf", mime_type="application/pdf")
def collateral_preview() -> bytes:
    """Current document's compiled PDF served from disk."""
    if not _ws.document_id:
        return b""
    from .store import DOCUMENTS_DIR

    pdf_path = DOCUMENTS_DIR / _ws.document_id / "output.pdf"
    if not pdf_path.exists():
        return b""
    return pdf_path.read_bytes()


@mcp.resource("collateral://exports/{export_id}.{ext}")
def collateral_export(export_id: str, ext: str) -> ResourceResult:
    """Rendered export (PDF or PNG) addressable by id. MIME is set per extension."""
    data = load_export(export_id, ext) or b""
    mime_type = _EXT_MIME.get(ext.lower(), "application/octet-stream")
    return ResourceResult([ResourceContent(data, mime_type=mime_type)])


@mcp.resource("collateral://assets/{filename}")
def collateral_asset(filename: str) -> ResourceResult:
    """Uploaded asset bytes, addressable by filename under ~/.collateral/assets/."""
    path = store.ASSETS_DIR / filename
    if not path.exists() or not path.is_file():
        return ResourceResult([ResourceContent(b"", mime_type="application/octet-stream")])
    return ResourceResult([ResourceContent(path.read_bytes(), mime_type=_mime_for(filename))])


# --- 1-2. Theme ---


@mcp.tool()
async def get_theme() -> dict:
    """Get the current document's theme (colors, fonts, spacing).

    Parses the theme block from the active document's Typst source.
    Returns a dict with keys: colors, fonts, spacing.
    """
    return _ws.get_theme()


@mcp.tool()
async def set_theme(updates: dict) -> WorkspaceState:
    """Update theme tokens in the current document.

    Merges the provided values into the source's theme block,
    auto-compiles, and auto-saves. Returns updated workspace state.

    Args:
        updates: Dict with optional keys: colors, fonts, spacing.
                 Each is a dict of token name to value.
    """
    return _ws.set_theme(updates)


# --- 3-7. Templates ---


@mcp.tool()
async def list_templates() -> list[TemplateInfo]:
    """List available templates with full variable schemas.

    Templates are scaffolds for common document types (proposal,
    invoice, resume, one-pager). Each includes variable definitions that
    can be filled via set_content.
    """
    return _ws.list_templates()


@mcp.tool()
async def get_template(template_id: str) -> dict:
    """Get a template's full details: info, source, and theme.

    Returns a dict with keys:
      - info: TemplateInfo with variable schema
      - source: the template.typ content
      - theme: ThemeData parsed from the source's theme block

    Args:
        template_id: Template identifier (e.g., "proposal", "invoice").
    """
    return template_mod.get_template(template_id)


@mcp.tool()
async def create_template(
    template_id: str,
    name: str,
    description: str,
    source: str,
    schema: dict | None = None,
) -> TemplateInfo:
    """Create a new template from scratch.

    Args:
        template_id: Unique identifier slug (e.g., "weekly-report").
        name: Human-readable template name.
        description: Brief description of the template's purpose.
        source: Typst source code for the template.
        schema: Optional variable schema dict defining template fields.
    """
    return _ws.create_template(template_id, name, description, source, schema)


@mcp.tool()
async def duplicate_template(
    template_id: str,
    new_id: str,
    new_name: str,
) -> TemplateInfo:
    """Duplicate an existing template with a new ID and name.

    Args:
        template_id: ID of the template to copy from.
        new_id: Unique identifier for the new template.
        new_name: Human-readable name for the new template.
    """
    return _ws.duplicate_template(template_id, new_id, new_name)


@mcp.tool()
async def delete_template(template_id: str) -> str:
    """Delete a user-created template.

    Built-in templates cannot be deleted.

    Args:
        template_id: ID of the template to delete.
    """
    _ws.delete_template(template_id)
    return f"Template '{template_id}' deleted."


# --- 8-12. Documents ---


@mcp.tool()
async def create_document(name: str, template_id: str | None = None) -> WorkspaceState:
    """Create a new document and set it as the active workspace.

    Optionally start from a template. If no template, creates a
    blank document. The document exists in memory until save_document
    persists it.

    Args:
        name: Human-readable document name (e.g., "Acme Proposal Q2").
        template_id: Optional template to scaffold from (e.g., "proposal", "invoice").
    """
    return _ws.create_document(name, template_id)


@mcp.tool()
async def list_documents() -> list[DocumentInfo]:
    """List saved documents with metadata (name, dates, template).

    Documents are stored in ~/.collateral/documents/.
    """
    return _ws.list_documents()


@mcp.tool()
async def open_document(document_id: str) -> WorkspaceState:
    """Load a saved document into the workspace.

    Args:
        document_id: Document identifier (slug from the document name).
    """
    return _ws.open_document(document_id)


@mcp.tool()
async def save_document(name: str | None = None) -> DocumentInfo:
    """Persist the current workspace to the filesystem.

    Args:
        name: Optional new name for the document.
    """
    return _ws.save_document(name)


@mcp.tool()
async def save_as_template(name: str, description: str = "") -> TemplateInfo:
    """Promote the current document's source into a new reusable template.

    The active document must have meaningful source content.

    Args:
        name: Human-readable name for the new template.
        description: Brief description of what the template is for.
    """
    return _ws.save_as_template(name, description)


@mcp.tool()
async def delete_document(document_id: str) -> str:
    """Delete a document from disk.

    Args:
        document_id: ID of the document to delete.
    """
    _ws.delete_document(document_id)
    return f"Document '{document_id}' deleted."


# --- 14-16. Editing ---


@mcp.tool()
async def get_workspace() -> WorkspaceState:
    """Get workspace metadata: document name, template, and theme.

    Does NOT include the Typst source — use get_source when you need
    to read or edit the document content. This lightweight call is
    ideal for checking document state without transferring the full source.
    """
    return _ws.get_state()


@mcp.tool()
async def get_source() -> str:
    """Get the current document's full Typst source code.

    Use this when you need to read the source for editing. For metadata
    and theme, use get_workspace instead (cheaper, no source transfer).
    """
    return _ws.get_source()


@mcp.tool()
async def patch_source(
    find: str | None = None,
    replace: str | None = None,
    edits: list[dict[str, str]] | None = None,
) -> WorkspaceState:
    """Surgical edit: find and replace text in the document source.

    THIS IS THE PREFERRED EDITING TOOL. Use it for all changes after the
    initial document creation. Supports single or batch edits.

    Single edit:
        patch_source(find="old text", replace="new text")

    Batch edit (multiple changes, one compilation):
        patch_source(edits=[
            {"find": "#v(section-gap)", "replace": "#v(12pt)"},
            {"find": "== Old Title", "replace": "== New Title"},
            {"find": "// end section", "replace": "#pagebreak()\\n// end section"}
        ])

    Each edit replaces the first occurrence only. Batch edits are applied
    sequentially and compiled once at the end. If any edit fails, all
    changes are rolled back. Auto-compiles and auto-saves.

    Args:
        find: Text to find (single edit mode). Mutually exclusive with edits.
        replace: Text to replace it with (single edit mode).
        edits: List of {find, replace} dicts (batch mode). Mutually exclusive with find/replace.
    """
    if edits is not None:
        if find is not None or replace is not None:
            raise ValueError("Use either find/replace OR edits, not both")
        # LLMs sometimes serialize the list as a JSON string
        if isinstance(edits, str):
            edits = json.loads(edits)
        return _ws.patch_source_batch(edits)
    if find is None or replace is None:
        raise ValueError("Provide either find+replace or edits")
    return _ws.patch_source(find, replace)


@mcp.tool()
async def set_source(source: str) -> WorkspaceState:
    """Replace the full Typst source. ONLY for initial document creation.

    Use this ONLY when writing a brand-new document from scratch or from
    imported content. For ALL subsequent edits — fixing spacing, changing
    text, adding sections, inserting page breaks — use patch_source instead.

    If you find yourself calling set_source on an existing document, STOP.
    Use patch_source(edits=[...]) to make targeted changes.

    Args:
        source: Complete Typst source code for the document.
    """
    return _ws.set_source(source)


@mcp.tool()
async def import_content(base64_data: str, filename: str) -> str:
    """Extract text from an uploaded file for use as source material.

    Supports PDF, TXT, MD, and TYP files. Returns the extracted text
    which the agent can then incorporate into the document.

    Args:
        base64_data: Base64-encoded file data.
        filename: Original filename with extension (e.g., "report.pdf", "notes.md").
    """
    return _ws.import_content(base64_data, filename)


# --- 16-18. Assets ---


@mcp.tool()
async def upload_asset(base64_data: str, filename: str) -> dict[str, str]:
    """Upload a binary asset (image, logo, icon) for use in documents.

    Assets are stored in ~/.collateral/assets/ and can be referenced
    in Typst source via their filename.

    Args:
        base64_data: Base64-encoded file data.
        filename: Filename to save as (e.g., "logo.png", "headshot.jpg").
    """
    return _ws.upload_asset(base64_data, filename)


@mcp.tool()
async def list_assets() -> list[str]:
    """List uploaded asset filenames available for use in documents."""
    return _ws.list_assets()


@mcp.tool()
async def delete_asset(filename: str) -> dict[str, str]:
    """Delete an uploaded asset by filename.

    Args:
        filename: The asset filename to delete.
    """
    return _ws.delete_asset(filename)


# --- 19-22. Voice & Components ---


@mcp.tool()
async def get_voice() -> str:
    """Get the current brand voice document.

    Returns the markdown content that defines the writing style, or
    an empty string if no voice has been configured.
    """
    return _ws.get_voice()


@mcp.tool()
async def set_voice(content: str) -> dict[str, str]:
    """Set the brand voice document that guides writing style.

    The voice content is appended to the skill resource so the agent
    automatically writes in the configured tone and style.

    Args:
        content: Markdown describing the brand voice, tone, and style guidelines.
    """
    return _ws.set_voice(content)


@mcp.tool()
async def get_components() -> str:
    """Get the current reusable Typst components.

    Returns the Typst source stored in components.typ, or an empty
    string if no components have been defined.
    """
    return _ws.get_components()


@mcp.tool()
async def set_components(source: str) -> dict[str, str]:
    """Save reusable Typst components (functions, styles, macros).

    Components are stored in ~/.collateral/components.typ and can be
    imported in document source. Use for shared layouts, callout boxes,
    or other reusable Typst snippets.

    Args:
        source: Typst source code defining reusable components.
    """
    return _ws.set_components(source)


# --- 23-24. Fonts ---


@mcp.tool()
async def list_fonts() -> list[str]:
    """List font families available to typst (system + custom).

    Custom fonts installed via install_font are stored in ~/.collateral/fonts/
    and automatically available for compilation.
    """
    return _ws.list_fonts()


@mcp.tool()
async def install_font(
    url: str | None = None,
    base64_data: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    """Install a font for use in documents.

    Downloads from a URL or accepts base64-encoded font data. Saves to
    ~/.collateral/fonts/ where it is automatically available for compilation.
    Supports .ttf, .otf, .ttc files. If the URL points to a .zip file,
    font files are extracted automatically.

    Args:
        url: URL to download the font from (e.g., Google Fonts download link).
        base64_data: Base64-encoded font file data (alternative to url).
        filename: Required when using base64_data. Optional with url.
    """
    return _ws.install_font(url=url, base64_data=base64_data, filename=filename)


# --- Rendering helpers ---


def _render_pdf(pdf_bytes: bytes, summary_name: str) -> ToolResult:
    size = len(pdf_bytes)
    # Typst emits one /Page object per page; /Pages is the catalog node.
    page_count = pdf_bytes.count(b"/Type /Page") - pdf_bytes.count(b"/Type /Pages")
    if page_count < 1:
        page_count = 1

    export_id, _ = store_export(pdf_bytes, "pdf")
    link = ResourceLink(
        type="resource_link",
        uri=AnyUrl(f"collateral://exports/{export_id}.pdf"),
        name=summary_name,
        mimeType="application/pdf",
        description=f"{summary_name} ({page_count} pages, {size // 1024 or 1}KB)",
        annotations=_USER_ONLY,
    )

    summary = f"{summary_name}: {page_count} page{'s' if page_count != 1 else ''}, {size} bytes"
    structured = {
        "export_id": export_id,
        "page_count": page_count,
        "size_bytes": size,
        "mime_type": "application/pdf",
    }
    return ToolResult(
        content=[TextContent(type="text", text=summary), link],
        structured_content=structured,
    )


# --- 25-27. Rendering ---


@mcp.tool()
async def preview(page: int | None = None) -> ToolResult:
    """Render the current document to a PDF preview.

    Returns a text summary and a resource_link to the PDF at
    ``collateral://exports/<id>.pdf``. Clients read via ``resources/read``
    and render with a native PDF viewer.

    Args:
        page: Optional page number (1-based) for a single-page preview.
    """
    from . import compiler

    if page is not None:
        pdf_bytes = compiler.compile_source(_ws.source, _ws.logo_data, page=page)
        return _render_pdf(pdf_bytes, f"Preview of {_ws.document_name} (page {page})")

    if _ws._cached_pdf is None:
        _ws._cached_pdf = compiler.compile_source(_ws.source, _ws.logo_data)
    return _render_pdf(_ws._cached_pdf, f"Preview of {_ws.document_name}")


@mcp.tool()
async def preview_template(template_id: str) -> ToolResult:
    """Preview a template without creating a document.

    Compiles the template source to PDF. Does not modify workspace state.

    Args:
        template_id: Template identifier (e.g., "proposal", "lead-magnet").
    """
    from . import compiler

    source = template_mod.get_source(template_id)
    pdf_bytes = compiler.compile_source(source, {})
    return _render_pdf(pdf_bytes, f"Template preview: {template_id}")


@mcp.tool()
async def export_pdf() -> ToolResult:
    """Export the current document as a PDF.

    Returns a text summary and a resource_link to ``collateral://exports/<id>.pdf``.
    """
    if _ws._cached_pdf is None:
        from . import compiler

        _ws._cached_pdf = compiler.compile_source(_ws.source, _ws.logo_data)
    return _render_pdf(_ws._cached_pdf, f"Export of {_ws.document_name}")


@mcp.tool()
async def compile_typst(source: str) -> ToolResult:
    """Compile raw Typst source to PDF. Bypasses workspace entirely.

    Args:
        source: Raw Typst source code.
    """
    from . import compiler

    pdf_bytes = compiler.compile_source(source)
    return _render_pdf(pdf_bytes, "Compiled Typst document")


# ---------------------------------------------------------------------------
# ASGI / Stdio entrypoints
# ---------------------------------------------------------------------------
_INLINE_SETTINGS_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Collateral Settings</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; padding: 0; color: #1a1a1a; background: transparent; font-size: 14px; line-height: 1.5; }
  h2 { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
  h3 { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; }
  .section { margin-bottom: 24px; padding: 16px; border: 1px solid #e5e5e5; border-radius: 8px; background: #fff; }
  .field { margin-bottom: 12px; }
  .field label { display: block; font-size: 12px; font-weight: 500; color: #666; margin-bottom: 4px; }
  .field input, .field select { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
  .field textarea { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; min-height: 100px; font-family: monospace; resize: vertical; }
  .color-row { display: flex; gap: 8px; align-items: center; }
  .color-row input[type=color] { width: 32px; height: 32px; padding: 0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
  .color-row input[type=text] { flex: 1; }
  button { padding: 8px 16px; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; background: #2563eb; color: #fff; }
  button:hover { background: #1d4ed8; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-secondary { background: #f3f4f6; color: #374151; }
  .btn-secondary:hover { background: #e5e7eb; }
  .assets-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
  .asset-tag { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #f3f4f6; border-radius: 4px; font-size: 12px; }
  .asset-tag button { padding: 0 4px; background: none; color: #999; font-size: 14px; }
  .asset-tag button:hover { color: #ef4444; }
  .status { font-size: 12px; margin-top: 8px; padding: 6px 10px; border-radius: 4px; }
  .status.ok { background: #f0fdf4; color: #166534; }
  .status.err { background: #fef2f2; color: #991b1b; }
  .loading { color: #999; font-style: italic; }
</style>
</head>
<body>
<div id="root" class="loading">Loading configuration...</div>
<script>
(function() {
  let _reqId = 0;
  const _pending = {};

  function callTool(name, args) {
    return new Promise((resolve, reject) => {
      const id = ++_reqId;
      _pending[id] = { resolve, reject };
      window.parent.postMessage({ jsonrpc: "2.0", id, method: "tools/call", params: { name, arguments: args || {} } }, "*");
    });
  }

  window.addEventListener("message", (e) => {
    const msg = e.data;
    if (!msg || !msg.jsonrpc) return;
    if (msg.id && _pending[msg.id]) {
      const { resolve, reject } = _pending[msg.id];
      delete _pending[msg.id];
      if (msg.error) reject(new Error(msg.error.message || "Tool call failed"));
      else resolve(msg.result);
    }
  });

  function parseResult(result) {
    if (result && result.content && result.content[0] && result.content[0].text) {
      try { return JSON.parse(result.content[0].text); } catch { return result.content[0].text; }
    }
    return result;
  }

  async function init() {
    const root = document.getElementById("root");
    try {
      const [themeResult, voiceResult, componentsResult, assetsResult] = await Promise.all([
        callTool("get_theme"),
        callTool("get_voice"),
        callTool("get_components"),
        callTool("list_assets"),
      ]);
      const theme = parseResult(themeResult) || {};
      const voice = parseResult(voiceResult) || "";
      const components = parseResult(componentsResult) || "";
      const assets = parseResult(assetsResult) || [];

      const colors = theme.colors || {};
      const fonts = theme.fonts || {};

      root.innerHTML = `
        <div class="section">
          <h2>Theme</h2>
          <h3>Colors</h3>
          <div class="field">
            <label>Primary</label>
            <div class="color-row">
              <input type="color" id="color-primary" value="${colors.primary || '#2563eb'}" />
              <input type="text" id="color-primary-text" value="${colors.primary || '#2563eb'}" />
            </div>
          </div>
          <div class="field">
            <label>Accent</label>
            <div class="color-row">
              <input type="color" id="color-accent" value="${colors.accent || '#7c3aed'}" />
              <input type="text" id="color-accent-text" value="${colors.accent || '#7c3aed'}" />
            </div>
          </div>
          <h3 style="margin-top:12px">Fonts</h3>
          <div class="field">
            <label>Heading Font</label>
            <input type="text" id="font-heading" value="${fonts.heading || ''}" placeholder="e.g. Inter, Helvetica" />
          </div>
          <div class="field">
            <label>Body Font</label>
            <input type="text" id="font-body" value="${fonts.body || ''}" placeholder="e.g. Georgia, serif" />
          </div>
          <button id="save-theme">Save Theme</button>
          <div id="theme-status"></div>
        </div>

        <div class="section">
          <h2>Brand Voice</h2>
          <div class="field">
            <label>Voice guidelines (Markdown)</label>
            <textarea id="voice-text">${typeof voice === "string" ? voice : ""}</textarea>
          </div>
          <button id="save-voice">Save Voice</button>
          <div id="voice-status"></div>
        </div>

        <div class="section">
          <h2>Reusable Components</h2>
          <div class="field">
            <label>Typst component source</label>
            <textarea id="components-text">${typeof components === "string" ? components : ""}</textarea>
          </div>
          <button id="save-components">Save Components</button>
          <div id="components-status"></div>
        </div>

        <div class="section">
          <h2>Assets</h2>
          <div class="assets-list" id="assets-list">
            ${(Array.isArray(assets) ? assets : []).map(a => '<span class="asset-tag">' + a + '<button data-asset="' + a + '">&times;</button></span>').join("")}
          </div>
          <div style="margin-top:12px">
            <input type="file" id="upload-asset" accept="image/*,.pdf,.svg" />
          </div>
          <div id="assets-status"></div>
        </div>
      `;
      root.className = "";

      // Sync color pickers with text inputs
      for (const key of ["primary", "accent"]) {
        const picker = document.getElementById("color-" + key);
        const text = document.getElementById("color-" + key + "-text");
        picker.addEventListener("input", () => { text.value = picker.value; });
        text.addEventListener("input", () => { picker.value = text.value; });
      }

      // Save theme
      document.getElementById("save-theme").addEventListener("click", async () => {
        const status = document.getElementById("theme-status");
        try {
          await callTool("set_theme", {
            updates: {
              colors: { primary: document.getElementById("color-primary-text").value, accent: document.getElementById("color-accent-text").value },
              fonts: { heading: document.getElementById("font-heading").value, body: document.getElementById("font-body").value },
            }
          });
          status.className = "status ok"; status.textContent = "Theme saved.";
        } catch (e) { status.className = "status err"; status.textContent = e.message; }
      });

      // Save voice
      document.getElementById("save-voice").addEventListener("click", async () => {
        const status = document.getElementById("voice-status");
        try {
          await callTool("set_voice", { content: document.getElementById("voice-text").value });
          status.className = "status ok"; status.textContent = "Voice saved.";
        } catch (e) { status.className = "status err"; status.textContent = e.message; }
      });

      // Save components
      document.getElementById("save-components").addEventListener("click", async () => {
        const status = document.getElementById("components-status");
        try {
          await callTool("set_components", { source: document.getElementById("components-text").value });
          status.className = "status ok"; status.textContent = "Components saved.";
        } catch (e) { status.className = "status err"; status.textContent = e.message; }
      });

      // Delete asset
      document.getElementById("assets-list").addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-asset]");
        if (!btn) return;
        const filename = btn.dataset.asset;
        if (!confirm("Delete " + filename + "?")) return;
        const status = document.getElementById("assets-status");
        try {
          await callTool("delete_asset", { filename });
          btn.closest(".asset-tag").remove();
          status.className = "status ok"; status.textContent = filename + " deleted.";
        } catch (e) { status.className = "status err"; status.textContent = e.message; }
      });

      // Upload asset
      document.getElementById("upload-asset").addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const status = document.getElementById("assets-status");
        const reader = new FileReader();
        reader.onload = async () => {
          const base64 = reader.result.split(",")[1];
          try {
            await callTool("upload_asset", { base64_data: base64, filename: file.name });
            const list = document.getElementById("assets-list");
            list.insertAdjacentHTML("beforeend", '<span class="asset-tag">' + file.name + '<button data-asset="' + file.name + '">&times;</button></span>');
            status.className = "status ok"; status.textContent = file.name + " uploaded.";
          } catch (e) { status.className = "status err"; status.textContent = e.message; }
        };
        reader.readAsDataURL(file);
      });

    } catch (e) {
      root.innerHTML = '<div class="status err">Failed to load settings: ' + e.message + '</div>';
      root.className = "";
    }
  }

  // Wait for bridge handshake, then init
  window.addEventListener("message", function onInit(e) {
    if (e.data && e.data.method === "ui/initialize") {
      window.removeEventListener("message", onInit);
      // Respond to handshake
      window.parent.postMessage({ jsonrpc: "2.0", id: e.data.id, result: {} }, "*");
      setTimeout(init, 100);
    }
  });
  // Fallback: init after 500ms if no handshake
  setTimeout(init, 500);
})();
</script>
</body>
</html>
"""

app = mcp.http_app()

# Stdio entrypoint for mpak / Claude Desktop
if __name__ == "__main__":
    print("Collateral Studio starting in stdio mode...", file=sys.stderr)
    mcp.run()
