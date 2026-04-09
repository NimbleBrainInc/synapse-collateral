"""Generate TypeScript types from Pydantic models.

Run: uv run python scripts/gen-types.py > ui/src/types.ts

This ensures UI types always match the server contract.
"""

from __future__ import annotations

from mcp_collateral.models import (
    AssetInfo,
    DocumentInfo,
    DocumentMeta,
    ExportResult,
    PagePreview,
    PreviewResult,
    SectionState,
    TemplateInfo,
    ThemeData,
    VariableDefinition,
    WorkspaceState,
)

PYDANTIC_TO_TS = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "Any": "unknown",
}


def ts_type(annotation: str) -> str:
    """Convert a Python type annotation string to TypeScript."""
    # Strip module prefixes (e.g., mcp_collateral.models.BrandColors → BrandColors)
    if "." in annotation and not annotation.startswith("list"):
        annotation = annotation.rsplit(".", 1)[-1]
    if annotation.startswith("list["):
        inner = annotation[5:-1]
        return f"{ts_type(inner)}[]"
    if annotation.endswith("| None") or annotation.startswith("Optional["):
        inner = annotation.replace(" | None", "").replace("Optional[", "").rstrip("]")
        return f"{ts_type(inner)} | null"
    return PYDANTIC_TO_TS.get(annotation, annotation)


def gen_interface(model_class: type) -> str:
    """Generate a TypeScript interface from a Pydantic BaseModel."""
    lines = [f"export interface {model_class.__name__} {{"]
    for name, field in model_class.model_fields.items():
        annotation = str(field.annotation).replace("typing.", "")
        # Clean up common patterns
        annotation = annotation.replace("<class '", "").replace("'>", "")
        annotation = annotation.replace("NoneType", "None")

        ts = ts_type(annotation)
        optional = "?" if field.default is not None and not field.is_required() else ""
        lines.append(f"  {name}{optional}: {ts};")
    lines.append("}")
    return "\n".join(lines)


MODELS = [
    ThemeData,
    VariableDefinition,
    TemplateInfo,
    AssetInfo,
    DocumentInfo,
    DocumentMeta,
    SectionState,
    WorkspaceState,
    PagePreview,
    PreviewResult,
    ExportResult,
]

print("// Auto-generated from Pydantic models — do not edit manually.")
print("// Run: uv run python scripts/gen-types.py > ui/src/types.ts")
print()
for model in MODELS:
    print(gen_interface(model))
    print()

# Also document the tool return types as a reference comment
print("// --- Tool Return Type Reference ---")
print("// list_templates() → TemplateInfo[]")
print("// create_template() → TemplateInfo")
print("// duplicate_template() → TemplateInfo")
print("// save_as_template() → TemplateInfo")
print("// create_document() → WorkspaceState")
print("// list_documents() → DocumentInfo[]")
print("// open_document() → WorkspaceState")
print("// save_document() → DocumentInfo")
print("// get_workspace() → WorkspaceState")
print("// set_content() → WorkspaceState")
print("// set_source() → WorkspaceState")
print("// get_theme() → { colors: Record<string,string>, fonts: Record<string,string>, spacing: Record<string,string> }")
print("// set_theme() → WorkspaceState")
print("// get_template() → { info: TemplateInfo, source: string, theme: ThemeData }")
print("// get_voice() → string")
print("// set_voice() → { status: string; path: string }")
print("// list_assets() → string[]")
print("// upload_asset() → { filename: string; path: string }")
print("// delete_asset() → { status: string; filename: string }")
print("// get_components() → string")
print("// set_components() → { status: string; path: string }")
print("// list_fonts() → string[]")
print("// install_font() → { installed: string[]; count: number; fonts_dir: string }")
print("// preview() → PreviewResult")
print("// export_pdf() → ExportResult")
print("// compile_typst() → ExportResult")
