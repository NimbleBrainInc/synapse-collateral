"""Filesystem-backed storage — v3 layout.

Storage tree under the data directory:
  components.typ              reusable Typst components
  voice.md                    brand voice document
  assets/                     user-uploaded images and files
  fonts/                      custom font files
  templates/<id>/             user templates (meta.json + template.typ)
  documents/<id>/             saved documents (meta.json + source.typ)
  _compile/                   transient compilation artifacts

Directory resolution: UPJACK_ROOT env var (set by NimbleBrain runtime),
falling back to ~/.collateral for standalone use.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import UTC, datetime
from importlib.resources import files as pkg_files
from pathlib import Path

from .models import DocumentInfo, DocumentMeta

# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------


def _resolve_base_dir() -> Path:
    """Resolve the data directory: UPJACK_ROOT env var or ~/.collateral."""
    root = os.environ.get("UPJACK_ROOT")
    return Path(root) if root else Path.home() / ".collateral"


BASE_DIR = _resolve_base_dir()
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = BASE_DIR / "fonts"
TEMPLATES_DIR = BASE_DIR / "templates"
DOCUMENTS_DIR = BASE_DIR / "documents"
COMPILE_DIR = BASE_DIR / "_compile"

_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _migrate_legacy_dir() -> None:
    """One-time migration from ~/.typst-pdf to ~/.collateral.

    Only runs when using the standalone default (~/.collateral).
    """
    if os.environ.get("UPJACK_ROOT"):
        return
    legacy = Path.home() / ".typst-pdf"
    if legacy.exists() and not BASE_DIR.exists():
        legacy.rename(BASE_DIR)


def _ensure_dirs() -> None:
    """Create the full directory tree if it doesn't exist."""
    _migrate_legacy_dir()
    for d in (ASSETS_DIR, FONTS_DIR, TEMPLATES_DIR, DOCUMENTS_DIR, COMPILE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _validate_filename(filename: str) -> None:
    """Reject filenames with path traversal or unsafe characters."""
    if not _SAFE_FILENAME_RE.match(filename):
        msg = f"Invalid filename: {filename!r} — only [a-zA-Z0-9._-] allowed"
        raise ValueError(msg)


def _doc_dir(document_id: str) -> Path:
    _ensure_dirs()
    return DOCUMENTS_DIR / document_id


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def read_components() -> str:
    """Read components.typ from BASE_DIR root, returning empty string if missing."""
    _ensure_dirs()
    path = BASE_DIR / "components.typ"
    if path.exists():
        return path.read_text()
    return ""


def write_components(source: str) -> Path:
    """Write components.typ to BASE_DIR root. Returns the path."""
    _ensure_dirs()
    path = BASE_DIR / "components.typ"
    path.write_text(source)
    return path


# ---------------------------------------------------------------------------
# Voice
# ---------------------------------------------------------------------------


def read_voice() -> str:
    """Read voice.md from BASE_DIR root, returning empty string if missing."""
    _ensure_dirs()
    path = BASE_DIR / "voice.md"
    if path.exists():
        return path.read_text()
    return ""


def write_voice(content: str) -> Path:
    """Write voice.md to BASE_DIR root. Returns the path."""
    _ensure_dirs()
    path = BASE_DIR / "voice.md"
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


def save_asset(filename: str, data: bytes) -> Path:
    """Save a binary asset. Returns the path to the written file."""
    _validate_filename(filename)
    _ensure_dirs()
    path = ASSETS_DIR / filename
    path.write_bytes(data)
    return path


def list_assets() -> list[str]:
    """Return sorted list of asset filenames."""
    _ensure_dirs()
    return sorted(p.name for p in ASSETS_DIR.iterdir() if p.is_file() and not p.name.startswith("."))


def delete_asset(filename: str) -> None:
    """Delete an asset by filename."""
    _validate_filename(filename)
    path = ASSETS_DIR / filename
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def _package_templates_dir() -> Path:
    """Return the path to the bundled package templates/ directory."""
    pkg = pkg_files("mcp_collateral")
    # pkg points to src/mcp_collateral; templates/ is two levels up
    return Path(str(pkg)).parent.parent / "templates"


def _package_assets_dir() -> Path:
    """Return the path to the bundled package assets/ directory."""
    pkg = pkg_files("mcp_collateral")
    return Path(str(pkg)).parent.parent / "assets"


def seed_templates() -> None:
    """Copy built-in templates into the user templates/ dir.

    Seeds missing templates and updates existing ones when the bundled
    template.typ is newer than the user's copy.
    """
    _ensure_dirs()

    src = _package_templates_dir()
    if not src.exists():
        return

    for template_dir in sorted(src.iterdir()):
        if not template_dir.is_dir():
            continue
        # Accept templates with either schema.json (legacy) or meta.json
        has_schema = (template_dir / "schema.json").exists()
        has_meta = (template_dir / "meta.json").exists()
        if not (has_schema or has_meta):
            continue

        dest = TEMPLATES_DIR / template_dir.name
        if not dest.exists():
            # New template — copy the whole directory
            shutil.copytree(template_dir, dest)
        else:
            # Existing template — update files that are newer in the package
            for src_file in template_dir.iterdir():
                if not src_file.is_file():
                    continue
                dest_file = dest / src_file.name
                if not dest_file.exists() or src_file.stat().st_mtime > dest_file.stat().st_mtime:
                    shutil.copy2(src_file, dest_file)

        # Migrate schema.json -> meta.json if needed
        dest_schema = dest / "schema.json"
        dest_meta = dest / "meta.json"
        if dest_schema.exists() and not dest_meta.exists():
            dest_schema.rename(dest_meta)


def seed_assets() -> None:
    """Copy built-in assets into the user assets/ dir if it exists.

    Idempotent: only copies files that don't already exist in the user dir.
    """
    _ensure_dirs()
    src = _package_assets_dir()
    if not src.exists():
        return

    for asset_file in sorted(src.iterdir()):
        if asset_file.is_file():
            dest = ASSETS_DIR / asset_file.name
            if not dest.exists():
                shutil.copy2(asset_file, dest)


def list_templates() -> list[dict]:
    """Return a list of template summaries (id, name, description)."""
    _ensure_dirs()
    seed_templates()
    templates = []
    for tdir in sorted(TEMPLATES_DIR.iterdir()):
        if not tdir.is_dir():
            continue
        meta_path = tdir / "meta.json"
        # Fall back to schema.json for legacy templates
        if not meta_path.exists():
            meta_path = tdir / "schema.json"
        if not meta_path.exists():
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        templates.append(
            {
                "id": tdir.name,
                "name": meta.get("name", tdir.name),
                "description": meta.get("description", ""),
            }
        )
    return templates


def save_template(
    template_id: str,
    name: str,
    description: str,
    source: str,
    schema: dict | None = None,
) -> Path:
    """Save or update a template. Returns the template directory path."""
    _ensure_dirs()
    tdir = TEMPLATES_DIR / template_id
    tdir.mkdir(parents=True, exist_ok=True)

    meta_data = schema or {}
    meta_data["name"] = name
    meta_data["description"] = description

    (tdir / "meta.json").write_text(json.dumps(meta_data, indent=2))
    (tdir / "template.typ").write_text(source)
    return tdir


def load_template(template_id: str) -> tuple[dict, str]:
    """Load a template. Returns (meta_dict, source_string)."""
    _ensure_dirs()
    tdir = TEMPLATES_DIR / template_id
    if not tdir.exists():
        msg = f"Template not found: {template_id}"
        raise FileNotFoundError(msg)

    meta_path = tdir / "meta.json"
    # Fall back to schema.json for legacy templates
    if not meta_path.exists():
        meta_path = tdir / "schema.json"

    with open(meta_path) as f:
        meta = json.load(f)
    source = (tdir / "template.typ").read_text()
    return meta, source


def delete_template(template_id: str) -> None:
    """Delete a template directory."""
    tdir = TEMPLATES_DIR / template_id
    if tdir.exists():
        shutil.rmtree(tdir)


def duplicate_template(template_id: str, new_id: str, new_name: str) -> Path:
    """Duplicate a template under a new id and name. Returns new template dir."""
    meta, source = load_template(template_id)
    return save_template(new_id, new_name, meta.get("description", ""), source, meta)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def list_documents() -> list[DocumentInfo]:
    """Return a list of document summaries."""
    _ensure_dirs()
    docs = []
    for meta_path in sorted(DOCUMENTS_DIR.glob("*/meta.json")):
        with open(meta_path) as f:
            data = json.load(f)
        meta = DocumentMeta(**data)
        docs.append(
            DocumentInfo(
                id=meta.id,
                name=meta.name,
                template_id=meta.template_id,
                created=meta.created,
                modified=meta.modified,
            )
        )
    return docs


def save_document(
    document_id: str,
    name: str,
    source: str,
    template_id: str | None = None,
    created: str | None = None,
) -> DocumentMeta:
    """Save or update a document. Returns the document metadata."""
    doc_dir = _doc_dir(document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)

    now = _now()
    meta = DocumentMeta(
        id=document_id,
        name=name,
        template_id=template_id,
        created=created or now,
        modified=now,
    )

    (doc_dir / "meta.json").write_text(json.dumps(meta.model_dump(), indent=2))
    (doc_dir / "source.typ").write_text(source)

    return meta


def load_document(document_id: str) -> tuple[DocumentMeta, str]:
    """Load a document. Returns (meta, source)."""
    doc_dir = _doc_dir(document_id)
    if not doc_dir.exists():
        msg = f"Document not found: {document_id}"
        raise FileNotFoundError(msg)

    with open(doc_dir / "meta.json") as f:
        meta = DocumentMeta(**json.load(f))

    source = (doc_dir / "source.typ").read_text()

    return meta, source


def delete_document(document_id: str) -> None:
    """Delete a document directory."""
    doc_dir = _doc_dir(document_id)
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
