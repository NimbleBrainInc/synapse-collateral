"""Stateless document operations.

Every public function takes ``document_id`` explicitly and reads/writes the
filesystem on each call. There is no in-process cursor — the document
being acted on is named in the call, never inferred from prior state.

This is the load-bearing fix for a class of bugs where an agent (or the
UI, or two parallel callers) believed they were editing document A while
the implicit "currently open document" had silently switched to B.

Disk layout (under ``store.DOCUMENTS_DIR / <document_id>``):
- ``meta.json``   — DocumentMeta (id, name, template_id, created, modified)
- ``source.typ``  — Typst source
- ``output.pdf``  — cached compile of source.typ; rewritten on every edit

Compile cache: ``output.pdf`` on disk IS the cache. ``render_pdf`` reads
it directly when its mtime is at least as recent as ``source.typ``;
otherwise compiles fresh and rewrites both. There is no in-memory cache.
"""

from __future__ import annotations

import difflib
import hashlib
import re

from . import compiler, store
from . import templates as template_mod
from . import theme as theme_mod
from .models import (
    DocumentInfo,
    DocumentMeta,
    DocumentState,
    NearestMatch,
    PatchSourceResult,
    SourceResponse,
    TemplateInfo,
    ThemeData,
)

# Fuzzy-match threshold for "did the agent mean this line?". Below this,
# we don't surface a nearest_match and tell the agent to call get_source.
_NEAREST_MATCH_THRESHOLD = 0.6
_CONTEXT_RADIUS_LINES = 3

BLANK_SOURCE = """\
#set document(title: "Untitled")
#set page(paper: "us-letter", margin: (top: 2cm, bottom: 2cm, left: 2.5cm, right: 2.5cm))
#set text(size: 11pt)

= Untitled Document

Start typing or ask the agent to build your document.
"""


# ---------------------------------------------------------------------------
# Document lifecycle
# ---------------------------------------------------------------------------


def create(name: str, template_id: str | None = None) -> DocumentState:
    """Create a new document on disk. Returns its state.

    The slug-collision check uses ``mkdir(exist_ok=False)`` to atomically
    claim the document directory, retrying with a numeric suffix on
    race. Two concurrent creates with the same name therefore can't both
    pick the same slug — one wins the directory, the other increments.
    """
    source = template_mod.get_source(template_id) if template_id else BLANK_SOURCE
    document_id = _claim_unique_slug(name)
    meta = store.save_document(
        document_id=document_id,
        name=name,
        source=source,
        template_id=template_id,
    )
    return _build_state(meta, source)


def get(document_id: str) -> DocumentState:
    """Read document state from disk."""
    meta, source = store.load_document(document_id)
    return _build_state(meta, source)


def save(document_id: str, name: str | None = None) -> DocumentInfo:
    """Persist (re-save) the document. Optionally rename. Returns DocumentInfo."""
    meta, source = store.load_document(document_id)
    saved = store.save_document(
        document_id=document_id,
        name=name or meta.name,
        source=source,
        template_id=meta.template_id,
        created=meta.created,
    )
    return DocumentInfo(
        id=saved.id,
        name=saved.name,
        template_id=saved.template_id,
        created=saved.created,
        modified=saved.modified,
    )


def delete(document_id: str) -> None:
    """Delete a document and its on-disk artifacts."""
    store.delete_document(document_id)


def list_all() -> list[DocumentInfo]:
    """List all saved documents."""
    return store.list_documents()


# ---------------------------------------------------------------------------
# Source — read / write
# ---------------------------------------------------------------------------


def get_source(document_id: str) -> SourceResponse:
    """Read the document's Typst source.

    Returns an object (not a bare string) so additional fields — most
    notably a future ``revision`` for optimistic-concurrency — can be
    added without breaking the wire contract.
    """
    _meta, source = store.load_document(document_id)
    return SourceResponse(document_id=document_id, source=source)


def set_source(document_id: str, source: str) -> DocumentState:
    """Replace the document's full Typst source. Compile, then persist.

    On compile failure raises ``RuntimeError`` — disk state is unchanged
    (we compile *before* writing, so a failed compile leaves the
    previous source.typ + output.pdf in place).
    """
    meta, _old = store.load_document(document_id)
    _compile_and_persist(meta, source)
    return _build_state(meta, source)


# ---------------------------------------------------------------------------
# Editing — patch_source (single + batch)
# ---------------------------------------------------------------------------


def patch_source(
    document_id: str,
    find: str,
    replace: str,
    validate: bool = True,
) -> PatchSourceResult:
    """Find-and-replace one occurrence in the document source.

    Never raises for text-not-found or compile-error — both are reported
    via ``PatchSourceResult.reason``. Raises only for programming errors
    (e.g. empty find string).
    """
    if not find:
        msg = "'find' must be a non-empty string"
        raise ValueError(msg)
    meta, source = store.load_document(document_id)
    if find not in source:
        return _not_found_result(source, find)
    new_source = source.replace(find, replace, 1)
    return _try_apply(meta, new_source, validate, query=find)


def patch_source_batch(
    document_id: str,
    edits: list[dict[str, str]],
    validate: bool = True,
) -> PatchSourceResult:
    """Apply multiple find/replace edits, compile once at the end.

    Each edit is applied against the source as it stands after prior
    edits in the same batch. If any edit's ``find`` is missing, no edits
    are committed; the result carries ``failed_edit_index``.
    """
    if not edits:
        msg = "edits must be a non-empty list"
        raise ValueError(msg)
    meta, source = store.load_document(document_id)
    new_source = source
    for i, edit in enumerate(edits):
        find = edit.get("find", "")
        replace = edit.get("replace", "")
        if not find:
            msg = f"Edit {i}: 'find' must be a non-empty string"
            raise ValueError(msg)
        if find not in new_source:
            return _not_found_result(new_source, find, failed_edit_index=i)
        new_source = new_source.replace(find, replace, 1)
    return _try_apply(meta, new_source, validate, query=None)


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


def get_theme(document_id: str) -> dict:
    """Parse and return theme data from the document's source."""
    _meta, source = store.load_document(document_id)
    return theme_mod.parse_theme(source)


def set_theme(document_id: str, updates: dict) -> DocumentState:
    """Update theme tokens in the document's source. Compiles + persists."""
    meta, source = store.load_document(document_id)
    new_source = theme_mod.update_theme(source, updates)
    _compile_and_persist(meta, new_source)
    return _build_state(meta, new_source)


# ---------------------------------------------------------------------------
# Promote document → template
# ---------------------------------------------------------------------------


def save_as_template(
    document_id: str,
    name: str,
    description: str = "",
) -> TemplateInfo:
    """Promote the document's source into a new reusable template."""
    _meta, source = store.load_document(document_id)
    if not source or source == BLANK_SOURCE:
        msg = "No meaningful source to save as a template."
        raise ValueError(msg)
    template_id = _slugify(name)
    return template_mod.create_template(template_id, name, source, description)


# ---------------------------------------------------------------------------
# Render — compile to PDF
# ---------------------------------------------------------------------------


def render_pdf(document_id: str, page: int | None = None) -> bytes:
    """Compile (or read cached) PDF for a document.

    Full document: read on-disk ``output.pdf`` if its mtime is at least
    as recent as ``source.typ``; otherwise compile fresh and rewrite.
    Single page: always compile fresh; not cached.
    """
    meta, source = store.load_document(document_id)
    if page is not None:
        return compiler.compile_source(source, {}, page=page)
    cached = _read_cached_pdf(document_id)
    if cached is not None:
        return cached
    return _compile_and_persist(meta, source)


def display_name(document_id: str) -> str:
    """Cheap accessor for display labels (e.g. preview captions)."""
    meta, _ = store.load_document(document_id)
    return meta.name


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_state(meta: DocumentMeta, source: str) -> DocumentState:
    """Materialize a DocumentState from an already-loaded meta + source.

    ``source_sha`` fingerprints the current source so that successive
    successful edits return distinct envelopes — see DocumentState.source_sha.
    """
    parsed = theme_mod.parse_theme(source)
    return DocumentState(
        document_id=meta.id,
        document_name=meta.name,
        template_id=meta.template_id,
        theme=ThemeData(
            colors=parsed.get("colors", {}),
            fonts=parsed.get("fonts", {}),
            spacing=parsed.get("spacing", {}),
        ),
        source_sha=hashlib.sha256(source.encode("utf-8")).hexdigest(),
    )


def _compile_and_persist(meta: DocumentMeta, source: str) -> bytes:
    """Compile source, then write source.typ + output.pdf + meta.json.

    Compile happens *before* any write, so a failure leaves disk
    untouched. Once compile succeeds, we save source first (the
    authoritative artifact) then output.pdf (the cache).
    """
    pdf = compiler.compile_source(source, {})
    store.save_document(
        document_id=meta.id,
        name=meta.name,
        source=source,
        template_id=meta.template_id,
        created=meta.created,
    )
    doc_dir = store.DOCUMENTS_DIR / meta.id
    (doc_dir / "output.pdf").write_bytes(pdf)
    return pdf


def _read_cached_pdf(document_id: str) -> bytes | None:
    """Return output.pdf bytes when it's at least as fresh as source.typ.

    Routes through ``store._doc_dir`` so document_id validation runs
    here too, not just on the write paths.
    """
    doc_dir = store._doc_dir(document_id)
    pdf_path = doc_dir / "output.pdf"
    src_path = doc_dir / "source.typ"
    if not pdf_path.exists() or not src_path.exists():
        return None
    # Strict <, not <=: _compile_and_persist writes source.typ before
    # output.pdf, so equal mtimes (possible on second-resolution
    # filesystems) mean the pair was written together and the cache is
    # fresh. validate=False edits write source.typ without rewriting
    # output.pdf, leaving src.mtime strictly newer — caught here.
    if pdf_path.stat().st_mtime < src_path.stat().st_mtime:
        return None
    return pdf_path.read_bytes()


def _try_apply(
    meta: DocumentMeta,
    new_source: str,
    validate: bool,
    query: str | None,
) -> PatchSourceResult:
    """Persist new source. Compile when validate=True; on compile failure,
    leave disk untouched and return a structured error."""
    if not validate:
        # Stage the source without compiling. Explicitly delete the cached
        # output.pdf so the next render recompiles instead of relying on
        # mtime ordering — second-resolution filesystems can tie source
        # and pdf mtimes when both writes happen in the same wall-clock
        # second, which would mask a stale cache.
        store.save_document(
            document_id=meta.id,
            name=meta.name,
            source=new_source,
            template_id=meta.template_id,
            created=meta.created,
        )
        pdf_path = store._doc_dir(meta.id) / "output.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
        return PatchSourceResult(
            applied=True,
            compiled=False,
            document=_build_state(meta, new_source),
        )
    try:
        _compile_and_persist(meta, new_source)
    except Exception as exc:  # noqa: BLE001 — surfacing typst error verbatim
        return _compile_error_result(query, str(exc))
    return PatchSourceResult(
        applied=True,
        compiled=True,
        document=_build_state(meta, new_source),
    )


def _not_found_result(
    source: str,
    query: str,
    failed_edit_index: int | None = None,
) -> PatchSourceResult:
    near = _nearest_line_match(source, query)
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


def _compile_error_result(query: str | None, error: str) -> PatchSourceResult:
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


def _nearest_line_match(source: str, query: str) -> NearestMatch | None:
    """Fuzzy-match the first line of *query* against source lines.

    autojunk=False: SequenceMatcher's heuristic gives wildly inflated
    ratios for lines much longer than the needle on Typst source.
    """
    if not source or not query:
        return None
    needle = query.split("\n", 1)[0].strip()
    if not needle:
        return None
    lines = source.splitlines()
    if not lines:
        return None
    best_ratio = 0.0
    best_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
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


def _slugify(name: str) -> str:
    """Convert a name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")[:64]


def _claim_unique_slug(name: str) -> str:
    """Atomically reserve a slug by creating its directory.

    ``mkdir(exist_ok=False)`` is the atomic primitive — only one caller
    can succeed for a given path, so concurrent creates with the same
    name don't collide. On collision we increment a suffix and retry.
    Bounded to keep a pathological loop visible.
    """
    store.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    base = _slugify(name)
    slug = base
    for counter in range(2, 1000):
        try:
            (store.DOCUMENTS_DIR / slug).mkdir(exist_ok=False)
            return slug
        except FileExistsError:
            slug = f"{base}-{counter}"
    msg = f"Could not allocate a unique document_id for {name!r}"
    raise RuntimeError(msg)
