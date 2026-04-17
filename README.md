# Collateral Studio

[![mpak](https://img.shields.io/badge/mpak-registry-blue)](https://mpak.dev/packages/@nimblebraininc/synapse-collateral?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![NimbleBrain](https://img.shields.io/badge/NimbleBrain-nimblebrain.ai-purple)](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![Discord](https://img.shields.io/badge/Discord-community-5865F2)](https://nimblebrain.ai/discord?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Typst-powered document generation with brand-aware templates, live preview, and conversational iteration.

**[View on mpak registry](https://mpak.dev/packages/@nimblebraininc/synapse-collateral?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)** | **Built by [NimbleBrain](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)**

## Tools

- **Theme**: `get_theme`, `set_theme`
- **Templates**: `list_templates`, `get_template`, `create_template`, `duplicate_template`, `delete_template`
- **Documents**: `create_document`, `list_documents`, `open_document`, `save_document`, `save_as_template`, `delete_document`
- **Workspace & Editing**: `get_workspace`, `get_source`, `patch_source`, `set_source`, `import_content`
- **Assets**: `upload_asset`, `list_assets`, `delete_asset`
- **Voice & Components**: `get_voice`, `set_voice`, `get_components`, `set_components`
- **Fonts**: `list_fonts`, `install_font`
- **Rendering**: `preview`, `preview_template`, `export_pdf`, `compile_typst`

Rendering tools return MCP `resource_link` content blocks pointing at the export resource template — not inline bytes. Clients fetch PDFs via `resources/read`.

## Resources

- `ui://collateral/main` — Studio UI rendered in the platform sidebar
- `ui://collateral/settings` — brand / voice / assets configuration panel
- `ui://collateral/preview.pdf` — current document compiled to PDF
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
