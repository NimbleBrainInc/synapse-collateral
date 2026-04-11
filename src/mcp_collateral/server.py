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
from mcp.types import Annotations, ImageContent, TextContent

from . import templates as template_mod
from .models import (
    DocumentInfo,
    ExportResult,
    PreviewResult,
    TemplateInfo,
    WorkspaceState,
)
from .workspace import Workspace

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


def _preview_result_to_content_blocks(
    result: PreviewResult,
) -> list[TextContent | ImageContent]:
    """Convert a PreviewResult to MCP content blocks with audience annotations.

    The text summary goes to both model and user. Each page image is
    annotated as user-only so base64 data stays out of the LLM context.
    """
    blocks: list[TextContent | ImageContent] = [
        TextContent(type="text", text=f"Preview rendered ({result.page_count} pages)"),
    ]
    for page in result.pages:
        if page.image_base64:
            blocks.append(
                ImageContent(
                    type="image",
                    data=page.image_base64,
                    mimeType="image/png",
                    annotations=_USER_ONLY,
                ),
            )
    return blocks


# --- 25-27. Rendering ---


@mcp.tool()
async def preview(page: int | None = None) -> list[TextContent | ImageContent]:
    """Render the current document to PNG preview images.

    Returns a text summary (for the model) and image blocks (for the user).

    Args:
        page: Optional page number (1-based) for single-page render.
    """
    result = _ws.preview(page=page, include_images=True)
    return _preview_result_to_content_blocks(result)


@mcp.tool()
async def preview_template(template_id: str) -> list[TextContent | ImageContent]:
    """Preview a template without creating a document.

    Compiles and renders the template source directly. Does not modify
    the workspace or create any files on disk. Returns a text summary
    (for the model) and image blocks (for the user).

    Args:
        template_id: Template identifier (e.g., "proposal", "lead-magnet").
    """
    result = _ws.preview_template(template_id, include_images=True)
    return _preview_result_to_content_blocks(result)


@mcp.tool()
async def export_pdf(include_data: bool = False) -> list[TextContent | ImageContent]:
    """Export the current document as a final PDF. Cached if unchanged.

    Returns a text summary (for the model). When include_data is true,
    also returns the base64 PDF as user-only content.

    Args:
        include_data: Include base64 PDF data in the response (for download).
    """
    result = _ws.export_pdf(include_data=include_data)
    blocks: list[TextContent | ImageContent] = [
        TextContent(
            type="text",
            text=f"Exported {result.filename} ({result.page_count} pages, {result.size_bytes} bytes)",
        ),
    ]
    if result.pdf_base64:
        blocks.append(
            TextContent(
                type="text",
                text=result.pdf_base64,
                annotations=_USER_ONLY,
            ),
        )
    return blocks


@mcp.tool()
async def compile_typst(source: str) -> ExportResult:
    """Compile raw Typst source to PDF. Bypasses workspace entirely.

    Args:
        source: Raw Typst source code.
    """
    return _ws.compile_typst(source)


# ASGI entrypoint for HTTP deployment
app = mcp.http_app()

# Stdio entrypoint for mpak / Claude Desktop
if __name__ == "__main__":
    print("Collateral Studio starting in stdio mode...", file=sys.stderr)
    mcp.run()
