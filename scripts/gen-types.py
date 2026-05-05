"""Generate TypeScript types from Pydantic models.

Run: uv run python scripts/gen-types.py > ui/src/types.ts

This ensures UI types always match the server contract.
"""

from __future__ import annotations

from mcp_collateral.models import (
    AssetInfo,
    DocumentInfo,
    DocumentMeta,
    DocumentState,
    NearestMatch,
    PatchSourceResult,
    SourceResponse,
    TemplateInfo,
    ThemeData,
)

PYDANTIC_TO_TS = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "Any": "unknown",
    "dict[str, str]": "Record<string, string>",
    "dict": "Record<string, unknown>",
}


def ts_type(annotation: str) -> str:
    """Convert a Python type annotation string to TypeScript."""
    # Handle ``T | None`` first so the inner conversion runs on T alone.
    if annotation.endswith(" | None"):
        return f"{ts_type(annotation[: -len(' | None')])} | null"
    if annotation.startswith("Optional["):
        return f"{ts_type(annotation[len('Optional[') : -1])} | null"
    # Strip module prefixes (e.g., mcp_collateral.models.ThemeData → ThemeData),
    # but preserve typing constructors like ``Literal[...]``.
    if "." in annotation and not annotation.startswith(("list", "dict", "Literal")):
        annotation = annotation.rsplit(".", 1)[-1]
    if annotation.startswith("list["):
        return f"{ts_type(annotation[5:-1])}[]"
    if annotation.startswith("Literal["):
        # Literal['a', 'b'] → "a" | "b"
        inner = annotation[len("Literal[") : -1]
        parts = [p.strip().strip("'\"") for p in inner.split(",")]
        return " | ".join(f'"{p}"' for p in parts)
    if annotation in PYDANTIC_TO_TS:
        return PYDANTIC_TO_TS[annotation]
    if annotation.startswith("dict["):
        inner = annotation[5:-1]
        if "," in inner:
            k, v = (s.strip() for s in inner.split(",", 1))
            return f"Record<{ts_type(k)}, {ts_type(v)}>"
    return annotation


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
    TemplateInfo,
    AssetInfo,
    DocumentInfo,
    DocumentMeta,
    DocumentState,
    SourceResponse,
    NearestMatch,
    PatchSourceResult,
]

print("// Auto-generated from Pydantic models — do not edit manually.")
print("// Run: uv run python scripts/gen-types.py > ui/src/types.ts")
print()
for model in MODELS:
    print(gen_interface(model))
    print()

# Document tool return types as a reference comment. Every read/write tool
# that targets a document takes document_id explicitly; there is no implicit
# cursor.
print("// --- Tool Return Type Reference ---")
print("// list_templates() → TemplateInfo[]")
print("// get_template(template_id) → { info, source, theme }")
print("// create_template(template_id, name, description, source, schema?) → TemplateInfo")
print("// duplicate_template(template_id, new_id, new_name) → TemplateInfo")
print("// delete_template(template_id) → string")
print("// save_as_template(document_id, name, description?) → TemplateInfo")
print("// create_document(name, template_id?) → DocumentState")
print("// list_documents() → DocumentInfo[]")
print("// save_document(document_id, name?) → DocumentInfo")
print("// delete_document(document_id) → string")
print("// get_workspace(document_id) → DocumentState")
print("// get_source(document_id) → SourceResponse")
print("// set_source(document_id, source) → DocumentState")
print("// patch_source(document_id, find?, replace?, edits?, validate?) → PatchSourceResult")
print("// get_theme(document_id) → { colors, fonts, spacing }")
print("// set_theme(document_id, updates) → DocumentState")
print("// import_content(base64_data, filename) → string")
print("// get_voice() → string")
print("// set_voice(content) → { status, path }")
print("// get_components() → string")
print("// set_components(source) → { status, path }")
print("// list_assets() → string[]")
print("// upload_asset(base64_data, filename) → { filename, path }")
print("// delete_asset(filename) → { status, filename }")
print("// list_fonts() → string[]")
print("// install_font(url?, base64_data?, filename?) → { installed, count, fonts_dir }")
print("// preview(document_id, page?) → ToolResult (resource_link to PDF)")
print("// preview_template(template_id) → ToolResult")
print("// export_pdf(document_id) → ToolResult")
print("// compile_typst(source) → ToolResult")
