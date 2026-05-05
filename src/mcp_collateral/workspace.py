"""Non-document workspace resources.

Document operations live in ``documents.py``. This module holds the
*workspace-scoped* resources that documents reference but aren't part
of any specific document:

- assets       — uploaded images / SVG / etc., addressable by filename
- voice        — brand voice markdown
- components   — reusable Typst components
- fonts        — installed font files
- imports      — file → text extraction (PDF, MD, TXT, TYP)
- exports      — short-lived rendered artifacts addressable by export_id

Every function is stateless and disk-backed. There is no Workspace class
and no in-process cursor — the legacy stateful model was the source of
the cross-document overwrite bugs that motivated the documents.py split.
"""

from __future__ import annotations

import base64
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

# ---------------------------------------------------------------------------
# Exports — short-lived rendered artifacts (PDFs, PNGs)
# ---------------------------------------------------------------------------

# Self-imposed cap on the voice body — a prompt-budget guard so voice.md
# stays small. Enforced in set_voice (raises; the settings UI disables Save
# over the cap), not by anything downstream.
MAX_VOICE_BYTES = 8 * 1024

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


# ---------------------------------------------------------------------------
# Imports — extract text from uploaded files
# ---------------------------------------------------------------------------


def import_content(base64_data: str, filename: str) -> str:
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


# ---------------------------------------------------------------------------
# Assets — user-uploaded images and binaries
# ---------------------------------------------------------------------------

_RASTER_IMAGE_EXTS = frozenset({"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"})


def _validate_image_bytes(data: bytes, filename: str) -> None:
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
            msg = f"Asset '{filename}' is not well-formed SVG ({exc}). Re-upload with valid bytes."
            raise ValueError(msg) from exc
        return
    if ext not in _RASTER_IMAGE_EXTS:
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


def upload_asset(base64_data: str, filename: str) -> dict[str, str]:
    """Decode base64 data and save as an asset. Returns path info.

    Image bytes are validated up-front (pymupdf for raster, XML parse
    for SVG). Corruption fails here rather than surfacing mid-compile
    many turns later.
    """
    data = base64.b64decode(base64_data)
    _validate_image_bytes(data, filename)
    path = store.save_asset(filename, data)
    return {"filename": filename, "path": str(path)}


def list_assets() -> list[str]:
    """Return sorted list of asset filenames."""
    return store.list_assets()


def delete_asset(filename: str) -> dict[str, str]:
    """Delete an asset by filename."""
    store.delete_asset(filename)
    return {"status": "deleted", "filename": filename}


# ---------------------------------------------------------------------------
# Voice — brand voice markdown
# ---------------------------------------------------------------------------


def get_voice() -> str:
    """Read the brand voice document."""
    return store.read_voice()


def set_voice(content: str) -> dict[str, str]:
    """Write the brand voice document.

    Empty (or whitespace-only) content clears the file (post-condition: file
    does not exist). Caps at 8 KiB UTF-8 — a self-imposed prompt-budget guard
    so the voice body stays small. Enforced here, not by anything downstream.
    """
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_VOICE_BYTES:
        msg = f"Voice exceeds {MAX_VOICE_BYTES} byte limit (got {len(encoded)} bytes)"
        raise ValueError(msg)
    if not content.strip():
        store.clear_voice()
        return {"status": "cleared"}
    path = store.write_voice(content)
    return {"status": "saved", "path": str(path)}


# ---------------------------------------------------------------------------
# Components — reusable Typst code
# ---------------------------------------------------------------------------


def get_components() -> str:
    """Read the reusable Typst components."""
    return store.read_components()


def set_components(source: str) -> dict[str, str]:
    """Write the reusable Typst components.

    Intentionally uncapped (unlike set_voice): components are Typst source a
    document imports, not text injected into the prompt, so a component library
    can legitimately be large.
    """
    path = store.write_components(source)
    return {"status": "saved", "path": str(path)}


# ---------------------------------------------------------------------------
# Fonts — list system + custom; install from URL or base64
# ---------------------------------------------------------------------------


def list_fonts() -> list[str]:
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

    return {"installed": saved, "count": len(saved), "fonts_dir": str(store.FONTS_DIR)}
