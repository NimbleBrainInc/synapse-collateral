"""Workspace state management — v3.

The workspace holds the currently open document. Documents have:
- A Typst source string (the primary artifact)
- A theme parsed from the source's ``// === THEME ===`` block
"""

from __future__ import annotations

import base64
import io
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from . import compiler, store
from . import templates as template_mod
from . import theme as theme_mod
from .models import (
    DocumentInfo,
    ExportResult,
    PagePreview,
    PreviewResult,
    TemplateInfo,
    ThemeData,
    WorkspaceState,
)

# Default blank document source
BLANK_SOURCE = """\
#set document(title: "Untitled")
#set page(paper: "us-letter", margin: (top: 2cm, bottom: 2cm, left: 2.5cm, right: 2.5cm))
#set text(size: 11pt)

= Untitled Document

Start typing or ask the agent to build your document.
"""


class Workspace:
    """Mutable workspace holding the currently open document."""

    def __init__(self) -> None:
        self.document_id: str | None = None
        self.document_name: str = "Untitled"
        self.template_id: str | None = None
        self.source: str = BLANK_SOURCE
        self.logo_data: dict[str, bytes] = {}
        self.created: str | None = None
        self._cached_pdf: bytes | None = None
        self._cached_pngs: list[bytes] | None = None

    # --- Introspection ---

    def get_state(self) -> WorkspaceState:
        parsed = theme_mod.parse_theme(self.source)
        theme = ThemeData(
            colors=parsed.get("colors", {}),
            fonts=parsed.get("fonts", {}),
            spacing=parsed.get("spacing", {}),
        )

        return WorkspaceState(
            document_id=self.document_id,
            document_name=self.document_name,
            template_id=self.template_id,
            theme=theme,
        )

    def get_source(self) -> str:
        """Return the current Typst source."""
        return self.source

    def reset(self) -> dict[str, str]:
        self.__init__()  # type: ignore[misc]
        return {"status": "reset"}

    # --- Theme ---

    def get_theme(self) -> dict:
        """Parse and return theme data from the current source."""
        return theme_mod.parse_theme(self.source)

    def set_theme(self, updates: dict) -> WorkspaceState:
        """Update theme tokens in the source, auto-compile, and auto-save."""
        self.source = theme_mod.update_theme(self.source, updates)
        self._invalidate()
        self._verify_compile()
        self._auto_save()
        return self.get_state()

    # --- Templates ---

    def list_templates(self) -> list[TemplateInfo]:
        return template_mod.list_templates()

    def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        source: str,
        schema: dict | None = None,
    ) -> TemplateInfo:
        return template_mod.create_template(template_id, name, source, description, schema)

    def duplicate_template(
        self,
        template_id: str,
        new_id: str,
        new_name: str,
    ) -> TemplateInfo:
        return template_mod.duplicate_template(template_id, new_id, new_name)

    def delete_template(self, template_id: str) -> None:
        template_mod.delete_template(template_id)

    def save_as_template(self, name: str, description: str = "") -> TemplateInfo:
        """Promote the current document's source into a new template."""
        if not self.source or self.source == BLANK_SOURCE:
            msg = "No meaningful source to save as a template."
            raise ValueError(msg)
        tid = _slugify(name)
        return template_mod.create_template(tid, name, self.source, description)

    # --- Documents ---

    def create_document(self, name: str, template_id: str | None = None) -> WorkspaceState:
        doc_id = _unique_slug(name)
        self.document_id = doc_id
        self.document_name = name
        self.template_id = template_id
        self.logo_data = {}
        self._invalidate()

        if template_id:
            self.source = template_mod.get_source(template_id)
        else:
            self.source = BLANK_SOURCE

        self._auto_save()
        return self.get_state()

    def list_documents(self) -> list[DocumentInfo]:
        return store.list_documents()

    def open_document(self, document_id: str) -> WorkspaceState:
        meta, source = store.load_document(document_id)
        self.document_id = meta.id
        self.document_name = meta.name
        self.template_id = meta.template_id
        self.source = source
        self.created = meta.created
        self.logo_data = {}
        self._invalidate()

        return self.get_state()

    def save_document(self, name: str | None = None) -> DocumentInfo:
        if not self.document_id:
            msg = "No document open. Call create_document first."
            raise ValueError(msg)
        if name:
            self.document_name = name

        meta = store.save_document(
            document_id=self.document_id,
            name=self.document_name,
            source=self.source,
            template_id=self.template_id,
            created=self.created,
        )
        self.created = meta.created
        return DocumentInfo(
            id=meta.id,
            name=meta.name,
            template_id=meta.template_id,
            created=meta.created,
            modified=meta.modified,
        )

    def delete_document(self, document_id: str) -> None:
        """Delete a document from disk. Clears workspace if it's the active doc."""
        store.delete_document(document_id)
        if self.document_id == document_id:
            self.__init__()  # type: ignore[misc]

    # --- Editing ---

    def set_source(self, source: str) -> WorkspaceState:
        """Replace the Typst source, compile, and auto-save."""
        original = self.source
        self.source = source
        self._invalidate()
        try:
            self._verify_compile()
            self._auto_save()
        except Exception:
            self.source = original
            self._invalidate()
            raise
        return self.get_state()

    def _find_nearby(self, needle: str, radius: int = 200) -> str:
        """Return a snippet of source near where *needle* was likely intended.

        Tries progressively shorter prefixes of the first line of *needle*
        to find an approximate match, then returns *radius* chars of context
        around that position.  Falls back to the first *radius* chars.
        """
        first_line = needle.split("\n", 1)[0][:60]
        for length in range(len(first_line), 9, -5):
            prefix = first_line[:length]
            pos = self.source.find(prefix)
            if pos != -1:
                start = max(0, pos - radius // 2)
                end = min(len(self.source), pos + radius // 2)
                return self.source[start:end]
        # Fallback: beginning of source
        return self.source[:radius]

    def patch_source(self, find: str, replace: str) -> WorkspaceState:
        """Find and replace in the source. Auto-compiles and auto-saves."""
        if find not in self.source:
            nearby = self._find_nearby(find)
            msg = f"Text not found in source: {find[:100]}...\nNearby source:\n{nearby}"
            raise ValueError(msg)
        original = self.source
        self.source = self.source.replace(find, replace, 1)  # replace first occurrence only
        self._invalidate()
        try:
            self._verify_compile()
            self._auto_save()
        except Exception:
            self.source = original
            self._invalidate()
            raise
        return self.get_state()

    def patch_source_batch(self, edits: list[dict[str, str]]) -> WorkspaceState:
        """Apply multiple find-replace edits, compile once at the end.

        Each edit is applied sequentially to the current source.
        If any find string is not found, raises ValueError with the
        failing edit index and text. Edits already applied before
        the failure are rolled back.
        """
        original = self.source
        for i, edit in enumerate(edits):
            find = edit.get("find", "")
            replace = edit.get("replace", "")
            if not find:
                self.source = original
                raise ValueError(f"Edit {i}: 'find' must be a non-empty string")
            if find not in self.source:
                nearby = self._find_nearby(find)
                self.source = original
                raise ValueError(
                    f"Edit {i}: text not found in source: {find[:100]}...\nNearby source:\n{nearby}"
                )
            self.source = self.source.replace(find, replace, 1)
        self._invalidate()
        try:
            self._verify_compile()
            self._auto_save()
        except Exception:
            self.source = original
            self._invalidate()
            raise
        return self.get_state()

    # --- Content Import ---

    def import_content(self, base64_data: str, filename: str) -> str:
        """Extract text from an uploaded file. Supports .pdf, .txt, .md, .typ."""
        data = base64.b64decode(base64_data)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "pdf":
            try:
                import pymupdf

                doc = pymupdf.open(stream=data, filetype="pdf")
                pages = [page.get_text() for page in doc]
                doc.close()
                return "\n\n".join(pages)
            except ImportError:
                # Fallback: crude extraction of parenthesized strings from PDF
                lines: list[str] = []
                for match in re.finditer(rb"\(([^)]+)\)", data):
                    try:
                        lines.append(match.group(1).decode("utf-8", errors="replace"))
                    except Exception:
                        pass
                if lines:
                    return "\n".join(lines)
                return data.decode("latin-1", errors="replace")
        elif ext in ("txt", "md", "typ"):
            return data.decode("utf-8", errors="replace")
        else:
            return data.decode("utf-8", errors="replace")

    # --- Assets ---

    def upload_asset(self, base64_data: str, filename: str) -> dict[str, str]:
        """Decode base64 data and save as an asset. Returns path info."""
        data = base64.b64decode(base64_data)
        path = store.save_asset(filename, data)
        return {"filename": filename, "path": str(path)}

    def list_assets(self) -> list[str]:
        """Return sorted list of asset filenames."""
        return store.list_assets()

    def delete_asset(self, filename: str) -> dict[str, str]:
        """Delete an asset by filename."""
        store.delete_asset(filename)
        return {"status": "deleted", "filename": filename}

    # --- Voice ---

    def get_voice(self) -> str:
        """Read the brand voice document."""
        return store.read_voice()

    def set_voice(self, content: str) -> dict[str, str]:
        """Write the brand voice document."""
        path = store.write_voice(content)
        return {"status": "saved", "path": str(path)}

    # --- Components ---

    def get_components(self) -> str:
        """Read the reusable Typst components."""
        return store.read_components()

    def set_components(self, source: str) -> dict[str, str]:
        """Write the reusable Typst components."""
        path = store.write_components(source)
        return {"status": "saved", "path": str(path)}

    def preview_template(self, template_id: str, include_images: bool = False) -> PreviewResult:
        """Preview a template without creating a document. Does not modify workspace state."""
        source = template_mod.get_source(template_id)
        pngs = compiler.compile_source(source, {}, output_format="png")
        return self._build_preview(pngs, include_images=include_images)

    # --- Rendering ---

    def preview(self, page: int | None = None, include_images: bool = False) -> PreviewResult:
        if self._cached_pngs is not None and page is None:
            return self._build_preview(self._cached_pngs, include_images=include_images)

        if page is not None:
            pngs = compiler.compile_source(
                self.source, self.logo_data, output_format="png", page=page
            )
            previews = [
                PagePreview(
                    page_number=page,
                    image_base64=base64.b64encode(d).decode() if include_images else None,
                )
                for d in pngs
            ]
            return PreviewResult(
                pages=previews,
                page_count=len(previews),
                message=f"Preview rendered ({len(previews)} page{'s' if len(previews) != 1 else ''})",
            )

        pngs = compiler.compile_source(self.source, self.logo_data, output_format="png")
        self._cached_pngs = pngs
        return self._build_preview(pngs, include_images=include_images)

    def export_pdf(self, include_data: bool = False) -> ExportResult:
        if self._cached_pdf is not None:
            return self._build_export(self._cached_pdf, include_data=include_data)

        pdf_pages = compiler.compile_source(self.source, self.logo_data, output_format="pdf")
        self._cached_pdf = pdf_pages[0]
        return self._build_export(self._cached_pdf, include_data=include_data)

    def compile_typst(self, source: str) -> ExportResult:
        pdf_pages = compiler.compile_source(source, output_format="pdf")
        return self._build_export(pdf_pages[0], filename="compiled.pdf", include_data=True)

    # --- Fonts ---

    def list_fonts(self) -> list[str]:
        """List font families available to typst (system + custom)."""
        typst_bin = compiler._find_typst()
        cmd = [typst_bin, "fonts", "--font-path", str(store.FONTS_DIR)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            msg = f"Failed to list fonts: {result.stderr.strip()}"
            raise RuntimeError(msg)
        families = sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
        return families

    def install_font(
        self,
        url: str | None = None,
        base64_data: str | None = None,
        filename: str | None = None,
    ) -> dict[str, Any]:
        """Download or decode a font and save to ~/.collateral/fonts/."""
        if not url and not base64_data:
            msg = "Provide either url or base64_data."
            raise ValueError(msg)

        store.FONTS_DIR.mkdir(parents=True, exist_ok=True)
        saved: list[str] = []
        font_exts = {".ttf", ".otf", ".ttc", ".woff2"}

        if url:
            with urlopen(url, timeout=30) as resp:  # noqa: S310
                data = resp.read()
            # Check if it's a zip
            if zipfile.is_zipfile(io.BytesIO(data)):
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    for name in zf.namelist():
                        p = Path(name)
                        if p.suffix.lower() in font_exts and not p.name.startswith("."):
                            dest = store.FONTS_DIR / p.name
                            dest.write_bytes(zf.read(name))
                            saved.append(p.name)
            else:
                fname = filename or Path(url).name or "font.ttf"
                dest = store.FONTS_DIR / Path(fname).name
                dest.write_bytes(data)
                saved.append(dest.name)
        else:
            if not filename:
                msg = "filename is required when using base64_data."
                raise ValueError(msg)
            data = base64.b64decode(base64_data)
            dest = store.FONTS_DIR / Path(filename).name
            dest.write_bytes(data)
            saved.append(dest.name)

        self._invalidate()
        return {"installed": saved, "count": len(saved), "fonts_dir": str(store.FONTS_DIR)}

    # --- Internal ---

    def _invalidate(self) -> None:
        self._cached_pdf = None
        self._cached_pngs = None

    def _verify_compile(self) -> None:
        """Compile to PDF + PNG, cache both, and write PDF to disk. Raises RuntimeError on failure."""
        pdf_pages = compiler.compile_source(self.source, self.logo_data, output_format="pdf")
        self._cached_pdf = pdf_pages[0]
        # Also compile PNGs so preview() never needs a second compile
        self._cached_pngs = compiler.compile_source(
            self.source, self.logo_data, output_format="png"
        )
        # Write the compiled PDF to disk for the preview resource
        if self.document_id:
            doc_dir = store.DOCUMENTS_DIR / self.document_id
            doc_dir.mkdir(parents=True, exist_ok=True)
            (doc_dir / "output.pdf").write_bytes(self._cached_pdf)

    def _auto_save(self) -> None:
        """Persist current state if a document is open."""
        if self.document_id:
            store.save_document(
                document_id=self.document_id,
                name=self.document_name,
                source=self.source,
                template_id=self.template_id,
                created=self.created,
            )

    @staticmethod
    def _build_preview(pngs: list[bytes], *, include_images: bool = False) -> PreviewResult:
        previews = [
            PagePreview(
                page_number=i + 1,
                image_base64=base64.b64encode(d).decode() if include_images else None,
            )
            for i, d in enumerate(pngs)
        ]
        count = len(previews)
        return PreviewResult(
            pages=previews,
            page_count=count,
            message=f"Preview rendered ({count} page{'s' if count != 1 else ''})",
        )

    @staticmethod
    def _build_export(
        pdf_bytes: bytes,
        filename: str = "document.pdf",
        *,
        include_data: bool = False,
    ) -> ExportResult:
        size = len(pdf_bytes)
        # Count pages by scanning PDF cross-reference for /Type /Page entries
        page_count = pdf_bytes.count(b"/Type /Page") - pdf_bytes.count(b"/Type /Pages")
        if page_count < 1:
            page_count = 1
        size_kb = size // 1024 or 1
        return ExportResult(
            pdf_base64=base64.b64encode(pdf_bytes).decode() if include_data else None,
            filename=filename,
            page_count=page_count,
            size_bytes=size,
            message=f"PDF exported ({page_count} page{'s' if page_count != 1 else ''}, {size_kb}KB)",
        )


def _slugify(name: str) -> str:
    """Convert a name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")[:64]


def _unique_slug(name: str) -> str:
    """Generate a slug that doesn't collide with existing documents."""
    base = _slugify(name)
    slug = base
    counter = 1
    while (store.DOCUMENTS_DIR / slug).exists():
        counter += 1
        slug = f"{base}-{counter}"
    return slug
