"""Collateral Studio — MCP server.

Documents are the primary entity. Templates are optional scaffolds.
The agent edits Typst source directly. Documents persist to
``~/.collateral/documents/`` (or ``$UPJACK_ROOT/documents/`` under
the NimbleBrain runtime).

Every read/write tool takes ``document_id`` explicitly. There is no
implicit cursor — see ``documents.py`` for the rationale.
"""

from __future__ import annotations

import sys
from importlib.resources import files
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import ResourceContent, ResourceResult
from fastmcp.tools import ToolResult
from mcp.types import Annotations, ResourceLink, TextContent
from pydantic import AnyUrl

from . import compiler, documents, store, workspace
from . import templates as template_mod
from .models import (
    DocumentInfo,
    DocumentState,
    PatchSourceResult,
    SourceResponse,
    TemplateInfo,
)
from .workspace import load_export, store_export

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
        "1. EVERY read/write tool takes document_id explicitly. There is no "
        "implicit cursor. Get document_id from create_document or "
        "list_documents.\n"
        "2. EDITING: Use patch_source(document_id, ...) for ALL edits after "
        "initial document creation. Use patch_source(document_id, edits=[...]) "
        "to batch multiple fixes in one call. NEVER use set_source to revise "
        "an existing document — it wastes tokens and risks breaking unrelated "
        "content.\n"
        "3. set_source is ONLY for writing the initial document from scratch "
        "or imported content.\n"
        "4. patch_source returns a structured PatchSourceResult — always check "
        "`applied` and `reason`. When applied=True/compiled=True, the edit is "
        "valid; do NOT call preview() to verify. When reason='text_not_found', "
        "read nearest_match.context and re-issue with the actual text. When "
        "reason='compile_error', fix the Typst error in compile_error and "
        "re-issue — source was rolled back.\n"
        "5. Only call preview(document_id) when the user asks to SEE the "
        "document.\n"
        "6. Never retry the same patch after text_not_found — read "
        "nearest_match first. The failure tells you exactly what's at that "
        "line.\n"
        "7. Use theme tokens (primary, ink, font-display, section-gap) — "
        "never hardcode rgb(), font names, or pt values in the document body.\n"
        "8. Read skill://collateral/usage for tool selection and error "
        "recovery."
    ),
)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("skill://collateral/usage")
def collateral_skill() -> str:
    """How to effectively use the Collateral Studio tools.

    Voice content is no longer spliced into this skill — it's served via
    `app://instructions` and the NimbleBrain platform wraps it in
    `<app-custom-instructions>` containment automatically. Voice now lives
    in `app://instructions`, not in this skill body.
    """
    return SKILL_CONTENT


# --- Custom Instructions (NimbleBrain platform contract) ---


@mcp.resource("app://instructions", mime_type="text/markdown")
def collateral_custom_instructions() -> str:
    """Per-bundle custom instructions for the NimbleBrain platform.

    NimbleBrain reads `app://instructions` from every active bundle on each
    prompt assembly. A non-empty body lands inside `<app-custom-instructions>`
    containment in the system prompt; empty omits the block. For collateral,
    this is the same body as `voice.md` — brand voice *is* the bundle's
    custom instructions for document generation.
    """
    return workspace.get_voice()


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
    """Collateral configuration panel — brand theme and custom instructions.

    Components and assets are managed inside the Collateral Studio app
    (Components/Assets views), not here. This panel is intentionally
    scoped to workspace-wide config the agent uses on every document.
    """
    if _SETTINGS_HTML.exists():
        return _SETTINGS_HTML.read_text()
    return _INLINE_SETTINGS_HTML  # defined at end of file to keep tools readable


@mcp.resource("collateral://exports/{export_id}.{ext}")
def collateral_export(export_id: str, ext: str) -> ResourceResult:
    """Rendered export (PDF or PNG) addressable by id. MIME is set per extension."""
    data = load_export(export_id, ext) or b""
    mime_type = _EXT_MIME.get(ext.lower(), "application/octet-stream")
    return ResourceResult([ResourceContent(data, mime_type=mime_type)])


@mcp.resource("collateral://assets/{filename}")
def collateral_asset(filename: str) -> ResourceResult:
    """Uploaded asset bytes, addressable by filename under ~/.collateral/assets/.

    Uploads pass through _validate_filename in store.py, but this handler is
    a separate trust boundary (resources can be read by anyone with the URI,
    not just whoever uploaded) so it re-enforces containment by resolving
    the path and rejecting anything outside ASSETS_DIR.
    """
    empty = ResourceResult([ResourceContent(b"", mime_type="application/octet-stream")])
    assets_root = store.ASSETS_DIR.resolve()
    try:
        candidate = (store.ASSETS_DIR / filename).resolve()
        candidate.relative_to(assets_root)
    except (ValueError, OSError):
        return empty
    if not candidate.is_file():
        return empty
    return ResourceResult([ResourceContent(candidate.read_bytes(), mime_type=_mime_for(filename))])


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_theme(document_id: str) -> dict:
    """Get a document's theme (colors, fonts, spacing).

    Parses the theme block from the document's Typst source.

    Args:
        document_id: Document identifier.
    """
    return documents.get_theme(document_id)


@mcp.tool()
async def set_theme(document_id: str, updates: dict) -> DocumentState:
    """Update theme tokens in a document. Auto-compiles, auto-saves.

    Args:
        document_id: Document identifier.
        updates: Dict with optional keys: colors, fonts, spacing.
                 Each is a dict of token name to value.
    """
    return documents.set_theme(document_id, updates)


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_templates() -> list[TemplateInfo]:
    """List available templates with full variable schemas."""
    return template_mod.list_templates()


@mcp.tool()
async def get_template(template_id: str) -> dict:
    """Get a template's full details: info, source, and theme.

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
    return template_mod.create_template(template_id, name, source, description, schema)


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
    return template_mod.duplicate_template(template_id, new_id, new_name)


@mcp.tool()
async def delete_template(template_id: str) -> str:
    """Delete a user-created template. Built-in templates cannot be deleted.

    Args:
        template_id: ID of the template to delete.
    """
    template_mod.delete_template(template_id)
    return f"Template '{template_id}' deleted."


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_document(name: str, template_id: str | None = None) -> DocumentState:
    """Create a new document. Returns the new document's state, including
    the assigned document_id that subsequent calls must use.

    Args:
        name: Human-readable document name (e.g., "Acme Proposal Q2").
        template_id: Optional template to scaffold from (e.g., "proposal").
    """
    return documents.create(name, template_id)


@mcp.tool()
async def list_documents() -> list[DocumentInfo]:
    """List saved documents with metadata. Use the returned ``id`` field
    as ``document_id`` for subsequent calls."""
    return documents.list_all()


@mcp.tool()
async def save_document(document_id: str, name: str | None = None) -> DocumentInfo:
    """Persist a document to disk. Optionally rename.

    Args:
        document_id: Document identifier.
        name: Optional new name for the document.
    """
    return documents.save(document_id, name)


@mcp.tool()
async def save_as_template(
    document_id: str,
    name: str,
    description: str = "",
) -> TemplateInfo:
    """Promote a document's source into a new reusable template.

    Args:
        document_id: Source document identifier.
        name: Human-readable name for the new template.
        description: Brief description of what the template is for.
    """
    return documents.save_as_template(document_id, name, description)


@mcp.tool()
async def delete_document(document_id: str) -> str:
    """Delete a document from disk.

    Args:
        document_id: Document identifier.
    """
    documents.delete(document_id)
    return f"Document '{document_id}' deleted."


# ---------------------------------------------------------------------------
# Reading state
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_workspace(document_id: str) -> DocumentState:
    """Get a document's metadata: name, template, and theme.

    Does NOT include the Typst source — use get_source when you need to
    read or edit the document content. This lightweight call is ideal
    for checking document state without transferring the full source.

    Args:
        document_id: Document identifier.
    """
    return documents.get(document_id)


@mcp.tool()
async def get_source(document_id: str) -> SourceResponse:
    """Get a document's full Typst source code.

    Returns ``{document_id, source}`` — an object, not a bare string —
    so callers can identify which document they're reading and
    additional fields can be added without breaking the contract.

    Args:
        document_id: Document identifier.
    """
    return documents.get_source(document_id)


# ---------------------------------------------------------------------------
# Editing
# ---------------------------------------------------------------------------


@mcp.tool()
async def patch_source(
    document_id: str,
    find: str | None = None,
    replace: str | None = None,
    edits: list[dict[str, str]] | None = None,
    validate: bool = True,
) -> PatchSourceResult:
    """Surgical edit: find and replace text in a document's source.

    THIS IS THE PREFERRED EDITING TOOL. Use it for all changes after the
    initial document creation. Supports single or batch edits.

    Single edit:
        patch_source(document_id, find="old text", replace="new text")

    Batch edit (multiple changes, one compilation):
        patch_source(document_id, edits=[
            {"find": "#v(section-gap)", "replace": "#v(12pt)"},
            {"find": "== Old Title", "replace": "== New Title"},
        ])

    Returns a structured PatchSourceResult. Inspect these fields:
      - applied:      True if the edit was committed.
      - compiled:     True if auto-compile succeeded (always False when
                      validate=False).
      - reason:       "text_not_found" → your find string is not in the
                      source. Read nearest_match.context (includes line
                      numbers) and re-issue with the actual text.
                      "compile_error" → the edit was substituted but Typst
                      failed to render; source was rolled back. Fix the
                      Typst error (check compile_error) and re-issue.
      - nearest_match: Line + similarity + ±3-line context for the closest
                       matching line. None when no close match exists.
      - suggestion:   Human-readable next step.
      - failed_edit_index: In batch mode, the index of the failing edit.
      - document:     Current DocumentState when applied=True.

    This tool never raises for text-not-found or compile-error — both are
    terminal states reported via ``reason``. Auto-saves on successful apply.

    Args:
        document_id: Document identifier.
        find: Text to find (single edit mode). Mutually exclusive with edits.
        replace: Text to replace it with (single edit mode).
        edits: List of {find, replace} dicts (batch mode). Mutually
               exclusive with find/replace.
        validate: When True (default), auto-compile after the edit and
                  roll back on compile failure. Set False to stage edits
                  that may not compile mid-way; call preview() when ready.
    """
    if edits is not None:
        if find is not None or replace is not None:
            raise ValueError("Use either find/replace OR edits, not both")
        return documents.patch_source_batch(document_id, edits, validate=validate)
    if find is None or replace is None:
        raise ValueError("Provide either find+replace or edits")
    return documents.patch_source(document_id, find, replace, validate=validate)


@mcp.tool()
async def set_source(document_id: str, source: str) -> DocumentState:
    """Replace a document's full Typst source. ONLY for initial creation.

    Use this ONLY when writing a brand-new document from scratch or from
    imported content. For ALL subsequent edits — fixing spacing, changing
    text, adding sections, inserting page breaks — use patch_source instead.

    If you find yourself calling set_source on an existing document, STOP.
    Use patch_source(document_id, edits=[...]) to make targeted changes.

    Args:
        document_id: Document identifier.
        source: Complete Typst source code for the document.
    """
    return documents.set_source(document_id, source)


@mcp.tool()
async def import_content(base64_data: str, filename: str) -> str:
    """Extract text from an uploaded file for use as source material.

    Supports PDF, TXT, MD, and TYP files. Returns the extracted text,
    which the agent can then incorporate into a document via set_source.

    Args:
        base64_data: Base64-encoded file data.
        filename: Original filename with extension (e.g., "report.pdf").
    """
    return workspace.import_content(base64_data, filename)


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


@mcp.tool()
async def upload_asset(base64_data: str, filename: str) -> dict[str, str]:
    """Upload a binary asset (image, logo, icon) for use in documents.

    Assets are stored in ~/.collateral/assets/ and can be referenced
    in Typst source via their filename.

    Args:
        base64_data: Base64-encoded file data.
        filename: Filename to save as (e.g., "logo.png", "headshot.jpg").
    """
    return workspace.upload_asset(base64_data, filename)


@mcp.tool()
async def list_assets() -> list[str]:
    """List uploaded asset filenames available for use in documents."""
    return workspace.list_assets()


@mcp.tool()
async def delete_asset(filename: str) -> dict[str, str]:
    """Delete an uploaded asset by filename.

    Args:
        filename: The asset filename to delete.
    """
    return workspace.delete_asset(filename)


# ---------------------------------------------------------------------------
# Voice & Components
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_voice() -> str:
    """Get the current brand voice document.

    Returns the markdown content that defines the writing style, or
    an empty string if no voice has been configured.
    """
    return workspace.get_voice()


@mcp.tool()
async def set_voice(content: str) -> dict[str, str]:
    """Set the brand voice document that guides writing style.

    Surfaced to the agent on every conversation turn via the platform's
    `app://instructions` contract — no manual skill splicing needed.
    Empty content clears the voice. Capped at 8 KiB UTF-8.

    Args:
        content: Markdown describing the brand voice, tone, and style.
    """
    try:
        return workspace.set_voice(content)
    except ValueError as err:
        # 8 KiB cap → return a structured tool error instead of letting
        # the exception cross the wire as a transport-level failure.
        return {"status": "error", "error": str(err)}


@mcp.tool()
async def get_components() -> str:
    """Get the current reusable Typst components.

    Returns the Typst source stored in components.typ, or an empty
    string if no components have been defined.
    """
    return workspace.get_components()


@mcp.tool()
async def set_components(source: str) -> dict[str, str]:
    """Save reusable Typst components (functions, styles, macros).

    Args:
        source: Typst source code defining reusable components.
    """
    return workspace.set_components(source)


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_fonts() -> list[str]:
    """List font families available to typst (system + custom)."""
    return workspace.list_fonts()


@mcp.tool()
async def install_font(
    url: str | None = None,
    base64_data: str | None = None,
    filename: str | None = None,
) -> dict[str, object]:
    """Install a font for use in documents.

    Downloads from a URL or accepts base64-encoded font data. Supports
    .ttf, .otf, .ttc files. If the URL points to a .zip file, font files
    are extracted automatically.

    Args:
        url: URL to download the font from.
        base64_data: Base64-encoded font file data (alternative to url).
        filename: Required when using base64_data. Optional with url.
    """
    return workspace.install_font(url=url, base64_data=base64_data, filename=filename)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


@mcp.tool()
async def preview(document_id: str, page: int | None = None) -> ToolResult:
    """Render a document to a PDF preview.

    Returns a text summary and a resource_link to the PDF at
    ``collateral://exports/<id>.pdf``. Clients read via ``resources/read``
    and render with a native PDF viewer.

    Args:
        document_id: Document identifier.
        page: Optional page number (1-based) for a single-page preview.
    """
    pdf_bytes = documents.render_pdf(document_id, page=page)
    name = documents.display_name(document_id)
    label = f"Preview of {name}" + (f" (page {page})" if page is not None else "")
    return _render_pdf(pdf_bytes, label)


@mcp.tool()
async def preview_template(template_id: str) -> ToolResult:
    """Preview a template without creating a document.

    Args:
        template_id: Template identifier (e.g., "proposal", "lead-magnet").
    """
    source = template_mod.get_source(template_id)
    pdf_bytes = compiler.compile_source(source, {})
    return _render_pdf(pdf_bytes, f"Template preview: {template_id}")


@mcp.tool()
async def export_pdf(document_id: str) -> ToolResult:
    """Export a document as a PDF.

    Args:
        document_id: Document identifier.
    """
    pdf_bytes = documents.render_pdf(document_id)
    name = documents.display_name(document_id)
    return _render_pdf(pdf_bytes, f"Export of {name}")


@mcp.tool()
async def compile_typst(source: str) -> ToolResult:
    """Compile raw Typst source to PDF. Bypasses the document store entirely.

    Args:
        source: Raw Typst source code.
    """
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
  h2 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
  h3 { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; }
  p.lede { font-size: 13px; color: #555; margin-bottom: 12px; }
  .section { margin-bottom: 24px; padding: 16px; border: 1px solid #e5e5e5; border-radius: 8px; background: #fff; }
  .field { margin-bottom: 12px; }
  .field label { display: block; font-size: 12px; font-weight: 500; color: #666; margin-bottom: 4px; }
  .field input, .field select { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
  .field textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; line-height: 1.5; min-height: 180px; font-family: ui-monospace, SFMono-Regular, monospace; resize: vertical; }
  .color-row { display: flex; gap: 8px; align-items: center; }
  .color-row input[type=color] { width: 32px; height: 32px; padding: 0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
  .color-row input[type=text] { flex: 1; }
  .row { display: flex; gap: 8px; align-items: center; margin-top: 10px; }
  .count { font-size: 12px; color: #777; margin-left: auto; }
  .count.over { color: #b91c1c; font-weight: 500; }
  button { padding: 8px 14px; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; background: #2563eb; color: #fff; }
  button:hover { background: #1d4ed8; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-secondary { background: #f3f4f6; color: #374151; }
  .btn-secondary:hover { background: #e5e7eb; }
  .status { font-size: 12px; padding: 6px 10px; border-radius: 4px; }
  .status.ok { background: #f0fdf4; color: #166534; }
  .status.err { background: #fef2f2; color: #991b1b; }
  .loading { color: #999; font-style: italic; padding: 16px; }
</style>
</head>
<body>
<div id="root" class="loading">Loading configuration…</div>
<script>
(function() {
  const MAX = 8 * 1024;
  let _reqId = 0;
  const _pending = {};

  function callTool(name, args) {
    return new Promise((resolve, reject) => {
      const id = ++_reqId;
      _pending[id] = { resolve, reject };
      window.parent.postMessage({ jsonrpc: "2.0", id, method: "tools/call", params: { name, arguments: args || {} } }, "*");
    });
  }
  function readResource(uri) {
    return new Promise((resolve, reject) => {
      const id = ++_reqId;
      _pending[id] = { resolve, reject };
      window.parent.postMessage({ jsonrpc: "2.0", id, method: "resources/read", params: { uri } }, "*");
    });
  }

  window.addEventListener("message", (e) => {
    const msg = e.data;
    if (!msg || !msg.jsonrpc) return;
    if (msg.id && _pending[msg.id]) {
      const { resolve, reject } = _pending[msg.id];
      delete _pending[msg.id];
      if (msg.error) reject(new Error(msg.error.message || "Request failed"));
      else resolve(msg.result);
    }
  });

  function parseResult(result) {
    if (result && result.content && result.content[0] && result.content[0].text) {
      try { return JSON.parse(result.content[0].text); } catch { return result.content[0].text; }
    }
    return result;
  }

  function utf8Bytes(s) { return new Blob([s]).size; }

  // Escape user-supplied values before HTML interpolation. & < > guard the
  // textarea body (Markdown containing </textarea> would otherwise break out
  // and truncate the saved value on next Save); " additionally guards
  // double-quoted attribute values (font names, theme tokens).
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  async function init() {
    const root = document.getElementById("root");
    try {
      const instructionsRes = await readResource("app://instructions");
      const instructions = (instructionsRes && instructionsRes.contents && instructionsRes.contents[0] && instructionsRes.contents[0].text) || "";

      root.innerHTML = `
        <div class="section">
          <h2>Custom Instructions</h2>
          <p class="lede">Brand voice, tone, and writing conventions the agent applies to every document it generates. Markdown supported.</p>
          <div class="field">
            <textarea id="ci-text" placeholder="e.g. Write in second person. Avoid jargon. Cite sources for engineering claims.">${esc(typeof instructions === "string" ? instructions : "")}</textarea>
          </div>
          <div class="row">
            <button id="save-ci">Save</button>
            <button class="btn-secondary" id="reset-ci">Reset</button>
            <span class="count" id="ci-count">0 / ${MAX.toLocaleString()} bytes</span>
          </div>
          <div id="ci-status" style="margin-top:8px"></div>
        </div>
      `;
      root.className = "";

      // Custom Instructions
      const ciText = document.getElementById("ci-text");
      const ciCount = document.getElementById("ci-count");
      const ciStatus = document.getElementById("ci-status");
      const ciSave = document.getElementById("save-ci");
      const ciReset = document.getElementById("reset-ci");
      let lastSaved = ciText.value;

      function updateCount() {
        const bytes = utf8Bytes(ciText.value);
        ciCount.textContent = bytes.toLocaleString() + " / " + MAX.toLocaleString() + " bytes";
        ciCount.className = "count" + (bytes > MAX ? " over" : "");
        ciSave.disabled = bytes > MAX || ciText.value === lastSaved;
        ciReset.disabled = ciText.value === lastSaved;
      }
      ciText.addEventListener("input", updateCount);
      updateCount();

      ciSave.addEventListener("click", async () => {
        ciStatus.className = ""; ciStatus.textContent = "";
        try {
          const res = await callTool("set_voice", { content: ciText.value });
          const parsed = parseResult(res);
          if (parsed && parsed.status === "error") throw new Error(parsed.error || "Save failed");
          lastSaved = ciText.value;
          ciStatus.className = "status ok"; ciStatus.textContent = parsed && parsed.status === "cleared" ? "Cleared." : "Saved.";
          updateCount();
          setTimeout(() => { ciStatus.textContent = ""; ciStatus.className = ""; }, 1500);
        } catch (e) { ciStatus.className = "status err"; ciStatus.textContent = e.message; }
      });
      ciReset.addEventListener("click", () => {
        ciText.value = lastSaved;
        ciStatus.className = ""; ciStatus.textContent = "";
        updateCount();
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
