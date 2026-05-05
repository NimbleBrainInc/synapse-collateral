## Tool Selection

Every read/write tool that targets a document takes `document_id` as
its first argument. There is no implicit cursor.

| User Intent | Tool |
|---|---|
| "what colors/fonts are we using?" | `get_theme(document_id)` |
| "change the primary color to blue" | `set_theme(document_id, {"primary": "#0055FF"})` |
| "use Inter for headings" | `set_theme(document_id, {"font-display": "Inter"})` |
| "what templates do you have?" | `list_templates()` |
| "show me the proposal template" | `get_template("proposal")` |
| "create a new template" | `create_template(id, name, description, source)` |
| "copy the proposal template" | `duplicate_template(id, new_id, new_name)` |
| "delete that template" | `delete_template(id)` |
| "make me a proposal" | `create_document("Acme Proposal", template_id="proposal")` |
| "make me a blank PDF" | `create_document("My Document")` |
| "show me my documents" | `list_documents()` |
| "save this" | `save_document(document_id)` |
| "save this as a template" | `save_as_template(document_id, "Weekly Report")` |
| "delete this document" | `delete_document(document_id)` |
| "what's in the doc?" | `get_workspace(document_id)` — metadata + theme (no source) |
| "show me the source" | `get_source(document_id)` — returns `{document_id, source}` |
| "change the headline" | `patch_source(document_id, "Old Headline", "New Headline")` |
| "add a section after pricing" | `get_source(document_id)` → modify → `set_source(document_id, new)` |
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
| "show me" | `preview(document_id)` |
| "export as PDF" | `export_pdf(document_id)` |
| "compile this Typst" | `compile_typst(source)` |

## Working with Templates

Templates are structural examples — they define layout, components, theme, and placeholder content. The agent reads a template's structure and writes new content into it.

When creating a document from a template, the template source is copied directly. The agent then rewrites content sections via `patch_source(document_id, ...)` or `set_source(document_id, ...)` while preserving the theme block and layout patterns.

## Error Recovery

`patch_source` never raises for not-found or compile errors — both are reported via the structured `PatchSourceResult`. Inspect `applied`, `compiled`, and `reason` every call.

### patch_source result reasons

| `reason` | What happened | Recovery |
|---|---|---|
| `null` (applied=True, compiled=True) | Edit committed, doc compiles. | Move on. Do not call `preview()` to verify. |
| `null` (applied=True, compiled=False) | `validate=False` was used; compile skipped. | Keep staging, call `preview(document_id)` when ready. |
| `"text_not_found"` | Your `find` string isn't in the source. | Read `nearest_match.context` (shows ±3 lines with line numbers). Re-issue with the exact text — or call `get_source(document_id)` if similarity is too low for `nearest_match` to appear. |
| `"compile_error"` | Edit was substituted but Typst rejected it. Source rolled back. | Read `compile_error` for the Typst error + line number. Fix the edit content, re-issue. |

### Typst compile errors (surfaced via `compile_error`)

| Error | Fix |
|---|---|
| "unknown font family: X" | `install_font(url=...)` or `set_theme(document_id, {"font-display": "Available Font"})` |
| "unknown variable: X" | Add `#let X = ...` to theme block via `set_theme(document_id, ...)` or fix in source |
| "file not found" (asset) | `list_assets()` → check filename → `upload_asset` or fix path |
| Generic compilation error | Read error line number → fix via `patch_source(document_id, ...)` |

### Asset uploads

`upload_asset` validates image bytes at upload time (pymupdf for raster, XML parse for SVG). A corrupt PNG is caught here, not 40 turns later when Typst tries to render it. If upload raises with "image validation", re-encode the asset and retry — the bytes you uploaded are corrupt.

## Document Lifecycle

1. `create_document(name, template_id?)` — auto-saves; **capture the returned `document_id`**
2. Edit via `patch_source(document_id, ...)` or `set_source(document_id, ...)` — auto-compiles, auto-saves
3. Adjust theme via `set_theme(document_id, updates)` — auto-compiles, auto-saves
4. `preview(document_id)` only when user asks to see it
5. `export_pdf(document_id)` to download
6. Later: `list_documents()` → use the `id` field as `document_id` to resume

## Anti-Patterns

- **NEVER use `set_source` to revise an existing document** — use `patch_source(document_id, edits=[...])` for batch fixes or `patch_source(document_id, find, replace)` for single changes. `set_source` is for initial creation only.
- **NEVER omit `document_id`** — there is no implicit cursor. Every doc-targeted call names its target.
- **Don't call `preview()` after every edit** — only when the user asks
- **Don't hardcode values in the document body** — always use theme tokens
- **Don't use `set_source` to change colors/fonts** — use `set_theme(document_id, ...)`
- **Don't use absolute paths for assets** — use `/assets/filename`
- **Don't forget to check `list_fonts()` before using a new font**
