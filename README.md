# Collateral Studio

[![mpak](https://img.shields.io/badge/mpak-registry-blue)](https://mpak.dev/packages/@nimblebraininc/synapse-collateral?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![NimbleBrain](https://img.shields.io/badge/NimbleBrain-nimblebrain.ai-purple)](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![Discord](https://img.shields.io/badge/Discord-community-5865F2)](https://nimblebrain.ai/discord?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Typst-powered document generation with brand-aware templates, live preview, and conversational iteration.

**[View on mpak registry](https://mpak.dev/packages/@nimblebraininc/synapse-collateral?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)** | **Built by [NimbleBrain](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)**

## Tools

Every read/write tool that targets a document takes `document_id` as
its first argument. There is no implicit cursor — see
[`src/mcp_collateral/documents.py`](src/mcp_collateral/documents.py)
for the rationale.

- **Theme**: `get_theme(document_id)`, `set_theme(document_id, updates)`
- **Templates**: `list_templates`, `get_template`, `create_template`, `duplicate_template`, `delete_template`
- **Documents**: `create_document(name, template_id?)`, `list_documents`, `save_document(document_id, name?)`, `save_as_template(document_id, name, description?)`, `delete_document(document_id)`
- **Reading state**: `get_workspace(document_id)`, `get_source(document_id)`
- **Editing**: `patch_source(document_id, ...)`, `set_source(document_id, source)`, `import_content(base64_data, filename)`
- **Assets**: `upload_asset`, `list_assets`, `delete_asset`
- **Voice & Components**: `get_voice`, `set_voice`, `get_components`, `set_components`
- **Fonts**: `list_fonts`, `install_font`
- **Rendering**: `preview(document_id, page?)`, `preview_template(template_id)`, `export_pdf(document_id)`, `compile_typst(source)`

Rendering tools return MCP `resource_link` content blocks pointing at the export resource template — not inline bytes. Clients fetch PDFs via `resources/read`.

## Resources

- `ui://collateral/main` — Studio UI rendered in the platform sidebar
- `ui://collateral/settings` — brand / voice / assets configuration panel
- `collateral://exports/{export_id}.{ext}` — rendered export bytes, MIME per extension
- `collateral://assets/{filename}` — uploaded asset bytes
- `skill://collateral/usage` — agent-facing usage guide
- `skill://collateral/reference` — tool catalog, error recovery, anti-patterns

## Built-in Templates

- `proposal` — Multi-page business proposal
- `one-pager` — Single-page product/service overview
- `invoice` — Invoice with line items and totals
- `resume` — Professional resume/CV

## Development

```bash
uv sync
uv run python -m mcp_collateral.server   # stdio mode
```
