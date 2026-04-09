# Collateral Studio

[![mpak](https://img.shields.io/badge/mpak-registry-blue)](https://mpak.dev/packages/@nimblebraininc/synapse-collateral?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![NimbleBrain](https://img.shields.io/badge/NimbleBrain-nimblebrain.ai-purple)](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![Discord](https://img.shields.io/badge/Discord-community-5865F2)](https://nimblebrain.ai/discord?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Typst-powered document generation with brand-aware templates, live preview, and conversational iteration.

**[View on mpak registry](https://mpak.dev/packages/@nimblebraininc/synapse-collateral?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)** | **Built by [NimbleBrain](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=synapse-collateral)**

## Tools

- **Workspace**: `get_workspace`, `reset_workspace`
- **Templates**: `list_templates`, `get_template_schema`, `set_template`
- **Brand**: `get_brand`, `set_brand`, `update_brand_colors`, `set_logo`, `list_brand_presets`, `load_brand_preset`
- **Content**: `set_content`, `update_section`, `get_content`, `list_sections`
- **Rendering**: `preview`, `preview_page`, `export_pdf`, `compile_typst`

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
