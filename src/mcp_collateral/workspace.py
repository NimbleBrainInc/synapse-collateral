"""Workspace state management — v3.

The workspace holds the currently open document. Documents have:
- A Typst source string (the primary artifact)
- A theme parsed from the source's ``// === THEME ===`` block
"""

from __future__ import annotations

import base64
import difflib
import io
import re
import secrets
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from . import compiler, store
from . import templates as template_mod
from . import theme as theme_mod
from .models import (
    DocumentInfo,
    NearestMatch,
    PatchSourceResult,
    TemplateInfo,
    ThemeData,
    WorkspaceState,
)

# Fuzzy-match threshold for "did the agent mean this line?". Below this, we
# don't surface a nearest_match and tell the agent to call get_source.
_NEAREST_MATCH_THRESHOLD = 0.6
_CONTEXT_RADIUS_LINES = 3

# Rendered artifacts are written here so tools can return resource_link
# references instead of inlining base64 bytes in tool results.
_EXPORT_TTL_SECONDS = 24 * 60 * 60


def _exports_dir() -> Path:
    # Resolve lazily so tests that monkeypatch store.BASE_DIR work.
    return store.BASE_DIR / "exports"


def _cleanup_stale_exports() -> None:
    try:
        d = _exports_dir()
        if not d.exists():
            return
        cutoff = time.time() - _EXPORT_TTL_SECONDS
        for p in d.iterdir():
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink()
            except OSError:
                pass
    except OSError:
        pass


def store_export(data: bytes, ext: str) -> tuple[str, Path]:
    """Persist rendered bytes under a short-lived export id. Returns (id, path)."""
    d = _exports_dir()
    d.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_exports()
    export_id = "exp_" + secrets.token_hex(8)
    path = d / f"{export_id}.{ext}"
    path.write_bytes(data)
    return export_id, path


def load_export(export_id: str, ext: str) -> bytes | None:
    """Load previously stored export bytes. Returns None if missing."""
    path = _exports_dir() / f"{export_id}.{ext}"
    if not path.exists():
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


# Module-level EXPORTS_DIR kept for backwards compat and test introspection.
EXPORTS_DIR = store.BASE_DIR / "exports"

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

    def _nearest_line_match(self, query: str) -> NearestMatch | None:
        """Fuzzy-match the first line of *query* against source lines.

        Uses difflib.SequenceMatcher on stripped lines. Returns None when
        the best similarity is below _NEAREST_MATCH_THRESHOLD — signalling
        that the agent should fall back to get_source.
        """
        if not self.source or not query:
            return None
        needle = query.split("\n", 1)[0].strip()
        if not needle:
            return None
        lines = self.source.splitlines()
        if not lines:
            return None
        best_ratio = 0.0
        best_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            # autojunk=False: accurate on Typst source; autojunk's heuristic
            # gives wildly inflated ratios for lines much longer than needle.
            ratio = difflib.SequenceMatcher(None, needle, stripped, autojunk=False).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = i
        if best_ratio < _NEAREST_MATCH_THRESHOLD:
            return None
        start = max(0, best_idx - _CONTEXT_RADIUS_LINES)
        end = min(len(lines), best_idx + _CONTEXT_RADIUS_LINES + 1)
        width = len(str(end))
        context_lines = [f"{str(i + 1).rjust(width)}│ {lines[i]}" for i in range(start, end)]
        return NearestMatch(
            line=best_idx + 1,
            similarity=round(best_ratio, 3),
            context="\n".join(context_lines),
        )

    def _not_found_result(
        self,
        query: str,
        failed_edit_index: int | None = None,
    ) -> PatchSourceResult:
        near = self._nearest_line_match(query)
        if near is not None:
            suggestion = (
                f"Line {near.line} is the closest match (similarity "
                f"{near.similarity}). Re-issue the patch using the exact "
                "text shown in the context, or call get_source to read "
                "the current document."
            )
        else:
            suggestion = (
                "No close match in the current source. Call get_source "
                "to read the document, then re-issue the patch with the "
                "exact text."
            )
        return PatchSourceResult(
            applied=False,
            compiled=False,
            reason="text_not_found",
            query=query,
            nearest_match=near,
            suggestion=suggestion,
            failed_edit_index=failed_edit_index,
        )

    def _compile_error_result(
        self,
        query: str | None,
        error: str,
    ) -> PatchSourceResult:
        return PatchSourceResult(
            applied=False,
            compiled=False,
            reason="compile_error",
            query=query,
            compile_error=error,
            suggestion=(
                "The edit was found and substituted, but Typst failed to "
                "render. Source was rolled back. Fix the Typst error "
                "(check the message for the offending line) and re-issue "
                "the patch. Pass validate=false to stage edits without "
                "auto-compiling."
            ),
        )

    def patch_source(
        self,
        find: str,
        replace: str,
        validate: bool = True,
    ) -> PatchSourceResult:
        """Find and replace in the source.

        Returns a PatchSourceResult describing the outcome. Does not raise
        for text_not_found or compile_error — both are reported via the
        ``reason`` field. Raises only for programming errors (e.g. empty
        find string).
        """
        if not find:
            msg = "'find' must be a non-empty string"
            raise ValueError(msg)
        if find not in self.source:
            return self._not_found_result(find)
        original = self.source
        self.source = self.source.replace(find, replace, 1)
        self._invalidate()
        if not validate:
            self._auto_save()
            return PatchSourceResult(
                applied=True,
                compiled=False,
                workspace=self.get_state(),
            )
        try:
            self._verify_compile()
        except Exception as exc:
            self.source = original
            self._invalidate()
            return self._compile_error_result(find, str(exc))
        self._auto_save()
        return PatchSourceResult(
            applied=True,
            compiled=True,
            workspace=self.get_state(),
        )

    def patch_source_batch(
        self,
        edits: list[dict[str, str]],
        validate: bool = True,
    ) -> PatchSourceResult:
        """Apply multiple find/replace edits, compile once at the end.

        Each edit is applied sequentially. If any edit's ``find`` is not
        present, no edits are committed and the result carries
        ``reason="text_not_found"`` with ``failed_edit_index`` identifying
        the offending entry. If compilation fails, all edits are rolled
        back and ``reason="compile_error"`` is returned.
        """
        if not edits:
            msg = "edits must be a non-empty list"
            raise ValueError(msg)
        original = self.source
        for i, edit in enumerate(edits):
            find = edit.get("find", "")
            replace = edit.get("replace", "")
            if not find:
                self.source = original
                msg = f"Edit {i}: 'find' must be a non-empty string"
                raise ValueError(msg)
            if find not in self.source:
                result = self._not_found_result(find, failed_edit_index=i)
                self.source = original
                return result
            self.source = self.source.replace(find, replace, 1)
        self._invalidate()
        if not validate:
            self._auto_save()
            return PatchSourceResult(
                applied=True,
                compiled=False,
                workspace=self.get_state(),
            )
        try:
            self._verify_compile()
        except Exception as exc:
            self.source = original
            self._invalidate()
            return self._compile_error_result(None, str(exc))
        self._auto_save()
        return PatchSourceResult(
            applied=True,
            compiled=True,
            workspace=self.get_state(),
        )

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

    _RASTER_IMAGE_EXTS = frozenset({"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"})

    def _validate_image_bytes(self, data: bytes, filename: str) -> None:
        """Reject corrupt image bytes before the asset hits disk.

        Raster formats are decoded via pymupdf (battle-tested MuPDF image
        pipeline). SVG is checked for XML well-formedness. Unknown
        extensions are trusted — non-image assets pass through.
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "svg":
            try:
                from xml.etree import ElementTree as ET

                ET.fromstring(data)
            except ET.ParseError as exc:
                msg = (
                    f"Asset '{filename}' is not well-formed SVG "
                    f"({exc}). Re-upload with valid bytes."
                )
                raise ValueError(msg) from exc
            return
        if ext not in self._RASTER_IMAGE_EXTS:
            return
        try:
            import pymupdf

            pymupdf.Pixmap(data)
        except Exception as exc:
            msg = (
                f"Asset '{filename}' failed image validation: {exc}. "
                "The bytes appear corrupt — re-upload a fresh copy. "
                "Validation happens at upload so you see the error "
                "now rather than later at compile time."
            )
            raise ValueError(msg) from exc

    def upload_asset(self, base64_data: str, filename: str) -> dict[str, str]:
        """Decode base64 data and save as an asset. Returns path info.

        Image bytes are validated up-front (pymupdf for raster, XML parse
        for SVG). Corruption fails here rather than surfacing mid-compile
        many turns later.
        """
        data = base64.b64decode(base64_data)
        self._validate_image_bytes(data, filename)
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

    def _verify_compile(self) -> None:
        """Compile to PDF, cache it, and write to disk. Raises RuntimeError on failure."""
        self._cached_pdf = compiler.compile_source(self.source, self.logo_data)
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
