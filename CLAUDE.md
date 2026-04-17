# Collateral Studio

Fat MCP server for document generation. Documents are the primary entity. The agent writes Typst; the server compiles it.

## Breaking changes

- **v0.4+ `export_pdf` no longer accepts `include_data: bool`.** Bytes always
  move out-of-band via the `collateral://exports/{id}.pdf` resource template —
  inlining base64 PDFs in tool results blew through the host's 1 MB cap.
  Direct MCP callers passing `include_data` will now fail input validation;
  LLM-facing behavior is unchanged.
- **v0.4+ rendering unified on PDF output.** `preview`, `preview_template`,
  `export_pdf`, and `compile_typst` all return a single `resource_link` block
  pointing at a PDF. The previous per-page PNG output path is gone.

## Commands

```bash
make run          # stdio mode
make run-http     # HTTP with reload
make check        # format + lint + test
make bundle       # build MCPB
make bump VERSION=0.2.0
```

## Architecture

**30 tools** organized by lifecycle: Theme (2), Templates (5), Documents (5), Editing (5), Assets (3), Voice & Components (4), Fonts (2), Rendering (3).

**Two editing modes:**
- `patch_source(find, replace)` — targeted text replacement (preferred for small edits)
- `set_source(typst_code)` — full source replacement for structural changes

The agent picks based on scope. Small edit → `patch_source`. Structural change → `get_source` to read, modify, `set_source`.

**No LLM in the server.** The host's agentic loop interprets natural language and calls tools. The server is a Typst compiler with state management.

**Brand model:**
- Global default: `~/.collateral/brand.json` (set via `configure_brand(..., set_as_default=true)`)
- Per-document: saved with the document, inherits from global on creation
- UI Brand view edits the global default

**Document storage:** `~/.collateral/documents/<slug>/` with `source.typ`, `brand.json`, `meta.json`.

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server, 13 tool definitions, resource registration |
| `workspace.py` | Mutable workspace state, document lifecycle, cache management |
| `compiler.py` | Typst compilation pipeline (source → PDF/PNG) |
| `starters.py` | Starter template registry, variable injection, source composition |
| `store.py` | Filesystem persistence (documents + global brand) |
| `brand.py` | Brand presets, Typst theme generation |
| `models.py` | Pydantic models for all tool I/O |
| `ui.py` | Self-contained HTML UI (3 views: documents, editor, brand) |
| `SKILL.md` | Embedded skill teaching agents how to use the tools |

## UI

Single HTML string served as `ui://collateral/main` with hash-based routing:
- `#/documents` — document list + new document dialog
- `#/editor` — full-width preview pane + action bar (Save, Export PDF)
- `#/brand` — global brand preset + color pickers

No sidebar forms. Chat is the input, preview is the output. The UI is for file management, preview, and direct-manipulation brand editing.

**Iframe constraint:** `prompt()` and `alert()` are blocked in sandboxed iframes. Use inline dialogs and visual feedback instead.

## Starters

Starters live in `templates/<id>/` (directory kept as `templates/` for Typst `--root` compatibility):
- `schema.json` — variable definitions
- `template.typ` — parameterized Typst source

To add a starter: create `templates/<id>/schema.json` + `template.typ`. Auto-discovered at startup.

## Design Principles

- Fewer tools = better agent performance
- Don't add tools to solve a skill problem — write a better skill
- Don't build formulaic UI for an agentic product — it fights the value prop
- The server stays dumb (no LLM). The skill teaches the agent. The agent does the thinking.
