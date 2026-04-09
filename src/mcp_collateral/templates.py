"""Template registry and variable injection.

Templates live in ~/.collateral/templates/ (user dir). On first access,
seed from the package's bundled templates/ and assets/ directories.
CRUD operations are delegated to store.py; this module owns preamble/compose
logic and theme parsing.
"""

from __future__ import annotations

import json

from . import store
from .models import TemplateInfo, ThemeData
from .theme import parse_theme

# ---------------------------------------------------------------------------
# Seeding (idempotent — called on first access)
# ---------------------------------------------------------------------------

_seeded = False


def _ensure_seeded() -> None:
    """Seed templates and assets from the package on first access."""
    global _seeded  # noqa: PLW0603
    if _seeded:
        return
    store.seed_templates()
    store.seed_assets()
    _seeded = True


# ---------------------------------------------------------------------------
# Template discovery
# ---------------------------------------------------------------------------


def list_templates() -> list[TemplateInfo]:
    """Return all templates from the user templates directory.

    Seeds from the bundled package templates and assets on first access
    if the user directory is empty.
    """
    _ensure_seeded()
    summaries = store.list_templates()
    templates: list[TemplateInfo] = []
    for s in summaries:
        tid = s["id"]
        meta_path = store.TEMPLATES_DIR / tid / "meta.json"
        # Fall back to schema.json for legacy templates
        if not meta_path.exists():
            meta_path = store.TEMPLATES_DIR / tid / "schema.json"
        if meta_path.exists():
            with open(meta_path) as f:
                data = json.load(f)
            templates.append(
                TemplateInfo(
                    id=tid,
                    name=data.get("name", tid),
                    description=data.get("description", ""),
                    page_count=data.get("page_count", 1),
                )
            )
    return templates


def get_template(template_id: str) -> dict:
    """Return template source and parsed theme for a template.

    Returns a dict with keys:
      - info: TemplateInfo with variable schema
      - source: the template.typ content
      - theme: ThemeData parsed from the source's theme block
    """
    _ensure_seeded()
    meta, source = store.load_template(template_id)
    info = TemplateInfo(
        id=template_id,
        name=meta.get("name", template_id),
        description=meta.get("description", ""),
        page_count=meta.get("page_count", 1),
    )
    parsed = parse_theme(source)
    theme = ThemeData(
        colors=parsed.get("colors", {}),
        fonts=parsed.get("fonts", {}),
        spacing=parsed.get("spacing", {}),
    )
    return {"info": info, "source": source, "theme": theme}


def get_source(template_id: str) -> str:
    """Return the template.typ content for a template."""
    _ensure_seeded()
    _meta, source = store.load_template(template_id)
    return source


# ---------------------------------------------------------------------------
# Template CRUD (thin wrappers around store)
# ---------------------------------------------------------------------------


def create_template(
    template_id: str,
    name: str,
    source: str,
    description: str = "",
    schema: dict | None = None,
) -> TemplateInfo:
    """Create a new template. Returns the TemplateInfo."""
    store.save_template(template_id, name, description, source, schema)
    return get_template(template_id)["info"]


def duplicate_template(
    template_id: str,
    new_id: str,
    new_name: str,
) -> TemplateInfo:
    """Duplicate an existing template. Returns the new TemplateInfo."""
    store.duplicate_template(template_id, new_id, new_name)
    return get_template(new_id)["info"]


def delete_template(template_id: str) -> None:
    """Delete a template by id."""
    store.delete_template(template_id)
