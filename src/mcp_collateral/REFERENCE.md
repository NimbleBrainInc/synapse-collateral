## Tool Selection

| User Intent | Tool |
|---|---|
| "what colors/fonts are we using?" | `get_theme()` |
| "change the primary color to blue" | `set_theme({"primary": "#0055FF"})` |
| "use Inter for headings" | `set_theme({"font-display": "Inter"})` |
| "what templates do you have?" | `list_templates()` |
| "show me the proposal template" | `get_template("proposal")` |
| "create a new template" | `create_template(id, name, description, source)` |
| "copy the proposal template" | `duplicate_template(id, new_id, new_name)` |
| "delete that template" | `delete_template(id)` |
| "make me a proposal" | `create_document("Acme Proposal", template_id="proposal")` |
| "make me a blank PDF" | `create_document("My Document")` |
| "show me my documents" | `list_documents()` |
| "open the Acme proposal" | `open_document("acme-proposal")` |
| "save this" | `save_document()` |
| "save this as a template" | `save_as_template("Weekly Report")` |
| "delete this document" | `delete_document(id)` |
| "what's in the doc?" | `get_workspace()` — metadata + theme (no source) |
| "show me the source" | `get_source()` — full Typst source |
| "change the headline" | `patch_source("Old Headline", "New Headline")` |
| "add a section after pricing" | `get_source()` → modify → `set_source(new)` |
| "here's a PDF to use as content" | `import_content(base64, filename)` |
| "upload our logo" | `upload_asset(base64, filename)` |
| "what assets do we have?" | `list_assets()` |
| "remove that old logo" | `delete_asset(filename)` |
| "set our writing voice" | `set_voice(content)` |
| "what's our voice guide?" | `get_voice()` |
| "add custom components" | `set_components(source)` |
| "show our components" | `get_components()` |
| "what fonts are available?" | `list_fonts()` |
| "install Inter font" | `install_font(url="https://fonts.google.com/download?family=Inter")` |
| "show me" | `preview()` |
| "export as PDF" | `export_pdf()` |
| "compile this Typst" | `compile_typst(source)` |

## Working with Templates

Templates are structural examples — they define layout, components, theme, and placeholder content. The agent reads a template's structure and writes new content into it.

When creating a document from a template, the template source is copied directly. The agent then rewrites content sections via `patch_source` or `set_source` while preserving the theme block and layout patterns.

## Error Recovery

`patch_source` never raises for not-found or compile errors — both are reported via the structured `PatchSourceResult`. Inspect `applied`, `compiled`, and `reason` every call.

### patch_source result reasons

| `reason` | What happened | Recovery |
|---|---|---|
| `null` (applied=True, compiled=True) | Edit committed, doc compiles. | Move on. Do not call `preview()` to verify. |
| `null` (applied=True, compiled=False) | `validate=False` was used; compile skipped. | Keep staging, call `preview()` when ready. |
| `"text_not_found"` | Your `find` string isn't in the source. | Read `nearest_match.context` (shows ±3 lines with line numbers). Re-issue with the exact text — or call `get_source()` if similarity is too low for `nearest_match` to appear. |
| `"compile_error"` | Edit was substituted but Typst rejected it. Source rolled back. | Read `compile_error` for the Typst error + line number. Fix the edit content, re-issue. |

### Typst compile errors (surfaced via `compile_error`)

| Error | Fix |
|---|---|
| "unknown font family: X" | `install_font(url=...)` or `set_theme({"font-display": "Available Font"})` |
| "unknown variable: X" | Add `#let X = ...` to theme block via `set_theme` or fix in source |
| "file not found" (asset) | `list_assets()` → check filename → `upload_asset` or fix path |
| Generic compilation error | Read error line number → fix via `patch_source` |

### Asset uploads

`upload_asset` validates image bytes at upload time (pymupdf for raster, XML parse for SVG). A corrupt PNG is caught here, not 40 turns later when Typst tries to render it. If upload raises with "image validation", re-encode the asset and retry — the bytes you uploaded are corrupt.

## Document Lifecycle

1. `create_document` (from template or blank) — auto-saves
2. Edit via `patch_source` or `set_source` — auto-compiles, auto-saves
3. Adjust theme via `set_theme` — auto-compiles, auto-saves
4. `preview()` only when user asks to see it
5. `export_pdf()` to download
6. Later: `list_documents()` → `open_document()` to resume

## Anti-Patterns

- **NEVER use `set_source` to revise an existing document** — use `patch_source(edits=[...])` for batch fixes or `patch_source(find, replace)` for single changes. `set_source` is for initial creation only.
- **Don't call `preview()` after every edit** — only when the user asks
- **Don't hardcode values in the document body** — always use theme tokens
- **Don't use `set_source` to change colors/fonts** — use `set_theme`
- **Don't use absolute paths for assets** — use `/assets/filename`
- **Don't forget to check `list_fonts()` before using a new font**
