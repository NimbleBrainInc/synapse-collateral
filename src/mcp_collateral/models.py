"""Pydantic models for all tool I/O."""

from __future__ import annotations

from pydantic import BaseModel, Field

# --- Theme ---


class ThemeData(BaseModel):
    """Parsed theme data from a template's theme.toml."""

    colors: dict[str, str] = Field(default_factory=dict)
    fonts: dict[str, str] = Field(default_factory=dict)
    spacing: dict[str, str] = Field(default_factory=dict)


# --- Templates ---


class TemplateInfo(BaseModel):
    """Returned by list_templates."""

    id: str
    name: str
    description: str = ""
    page_count: int = 1
    created: str = ""
    modified: str = ""


# --- Assets ---


class AssetInfo(BaseModel):
    """Metadata for a template or document asset file."""

    filename: str
    size_bytes: int
    modified: str = ""


# --- Documents ---


class DocumentMeta(BaseModel):
    """Persisted document metadata."""

    id: str
    name: str
    template_id: str | None = None
    created: str = ""
    modified: str = ""


class DocumentInfo(BaseModel):
    """Returned by list_documents."""

    id: str
    name: str
    template_id: str | None = None
    created: str = ""
    modified: str = ""


# --- Workspace ---


class WorkspaceState(BaseModel):
    """The single introspection response — everything the agent needs."""

    document_id: str | None = None
    document_name: str | None = None
    template_id: str | None = None
    theme: ThemeData = Field(default_factory=ThemeData)
