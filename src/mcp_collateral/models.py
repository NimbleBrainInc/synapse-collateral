"""Pydantic models for all tool I/O."""

from __future__ import annotations

from typing import Literal

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


# --- Editing (patch_source) ---


class NearestMatch(BaseModel):
    """Fuzzy-matched context for a failed patch query."""

    line: int
    similarity: float
    context: str


PatchFailureReason = Literal["text_not_found", "compile_error"]


class PatchSourceResult(BaseModel):
    """Structured response from patch_source.

    Three terminal states:
    - applied=True, compiled=True  → edit committed, document compiles
    - applied=True, compiled=False → validate=False was used; compile skipped
    - applied=False, reason=...    → edit rejected (text_not_found or compile_error);
                                     source unchanged
    """

    applied: bool
    compiled: bool
    reason: PatchFailureReason | None = None
    query: str | None = None
    nearest_match: NearestMatch | None = None
    suggestion: str | None = None
    compile_error: str | None = None
    failed_edit_index: int | None = None
    workspace: WorkspaceState | None = None
