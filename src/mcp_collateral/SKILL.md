# Collateral Studio

30 tools. Documents are the primary entity. Theme lives in the source.

<!-- VOICE -->

## Theme Discipline

Every `.typ` file has a `// === THEME ===` block that defines all design tokens:

```typst
// === THEME ===
#let primary = rgb("#0066FF")
#let accent = rgb("#00D4FF")
#let ink = rgb("#0F172A")
#let font-display = "Plus Jakarta Sans"
#let font-body = "Avenir Next"
#let pad-x = 56pt
#let section-gap = 28pt
// === END THEME ===
```

**This is the single source of truth.** There is no external config file. The source IS the design.

### Rules — never violate these

1. **No hardcoded colors in the document body.** Every `rgb(...)` or color value must be a token from the theme block. If you need a new color, add it to the theme block first, then reference the token.
2. **No hardcoded font names in the document body.** Use `font-display`, `font-body`, `font-code`. If a different font is needed, add/update the token in the theme block.
3. **No hardcoded spacing values in the document body.** Use `section-gap`, `pad-x`, `pad-y`, `label-gap`, `headline-gap`, `para-gap`, `card-gap`. Need a new spacing value? Add a token.
4. **Assets referenced as `/assets/filename`** — never absolute paths or `../`.
5. **Never remove or reformat the `// === THEME ===` markers.**

### Changing the theme

- `get_theme()` — parse the theme block, returns `{colors, fonts, spacing}`
- `set_theme(updates)` — merge changes into the theme block, auto-compiles, auto-saves

Example: user says "make it more blue"
```
set_theme({"primary": "#0055FF", "accent": "#3B82F6"})
```

Example: user says "use Inter for headings"
```
set_theme({"font-display": "Inter"})
```

Always check `list_fonts()` before setting a font. Install missing fonts via `install_font`.

## Editing — Tool Selection Rules

### The two editing modes

1. **`set_source(source)`** — Write the ENTIRE document. Use ONLY for:
   - Initial document creation from a template
   - Writing a brand-new document from imported content
   - **Never for revisions.** If the document already exists, use `patch_source`.

2. **`patch_source(...)`** — Surgical find-and-replace. Use for ALL changes after creation:
   - Fixing spacing, margins, gaps
   - Changing text, headlines, section content
   - Adding/removing page breaks
   - Inserting new sections
   - Fixing compilation errors
   - **Anything that modifies an existing document**

### Batch edits (preferred for multi-change fixes)

When you need to fix multiple things, use batch mode — one call, one compilation:

```
patch_source(edits=[
    {"find": "#v(section-gap)", "replace": "#v(12pt)"},
    {"find": "== Old Title", "replace": "== New Title"},
    {"find": "// end intro", "replace": "#pagebreak()\n// end intro"}
])
```

This is dramatically more efficient than calling `set_source` with the entire 500-line document rewritten. It also can't accidentally break content you didn't intend to change.

### Whitespace matters — exact matching

`patch_source` uses **exact string matching**. The `find` text must match the source byte-for-byte, including newlines and indentation.

**Common mistake:** Collapsing multi-line text into a single line.

Wrong: `find="text#linebreak()more text"` (newline + indentation collapsed)
Right: `find="text#linebreak()\n        more text"` (preserves the actual whitespace)

**Best practice:** Use shorter find strings that stay on a single line. Instead of matching a full multi-line paragraph, match just the unique phrase on one line.

If unsure about exact whitespace, call `get_source()` first and copy the text exactly.

### Single edit

For a single change, use the simple form:

```
patch_source(find="#v(78pt)", replace="#v(24pt)")
```

### Quick reference

| Change scope | Tool | Why |
|---|---|---|
| Multiple targeted fixes | `patch_source(edits=[...])` | One call, one compile, surgical |
| Single text replacement | `patch_source(find, replace)` | Minimal tokens |
| Theme colors/fonts/spacing | `set_theme(updates)` | Updates theme block only |
| Initial document content | `set_source(source)` | Full document, one-time only |
| Read the source | `get_source()` | Returns full Typst source |
| Read metadata + theme | `get_workspace()` | Lightweight, no source |

**`set_source` and `patch_source` compile automatically.** If the tool succeeds, the edit is valid. Only call `preview()` when the user asks to see the document.

## Content Import

- `import_content(base64_data, filename)` — extracts text from uploaded files (PDF, TXT, MD, TYP)
- The agent receives the extracted text and incorporates it into the document via `set_source`
- When creating a document from imported content, choose a template that matches the content structure, then rewrite the content sections while preserving the template's layout and theme

For detailed tool selection, error recovery, and anti-patterns, read the `skill://collateral/reference` resource.
