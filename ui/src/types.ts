// Auto-generated from Pydantic models — do not edit manually.
// Run: uv run python scripts/gen-types.py > ui/src/types.ts

export interface ThemeData {
  colors?: Record<string, string>;
  fonts?: Record<string, string>;
  spacing?: Record<string, string>;
}

export interface TemplateInfo {
  id: string;
  name: string;
  description?: string;
  page_count?: number;
  created?: string;
  modified?: string;
}

export interface AssetInfo {
  filename: string;
  size_bytes: number;
  modified?: string;
}

export interface DocumentInfo {
  id: string;
  name: string;
  template_id: string | null;
  created?: string;
  modified?: string;
}

export interface DocumentMeta {
  id: string;
  name: string;
  template_id: string | null;
  created?: string;
  modified?: string;
}

export interface DocumentState {
  document_id: string | null;
  document_name: string | null;
  template_id: string | null;
  theme?: ThemeData;
}

export interface SourceResponse {
  document_id: string;
  source: string;
}

export interface NearestMatch {
  line: number;
  similarity: number;
  context: string;
}

export interface PatchSourceResult {
  applied: boolean;
  compiled: boolean;
  reason: "text_not_found" | "compile_error" | null;
  query: string | null;
  nearest_match: NearestMatch | null;
  suggestion: string | null;
  compile_error: string | null;
  failed_edit_index: number | null;
  document: DocumentState | null;
}

// --- Tool Return Type Reference ---
// list_templates() → TemplateInfo[]
// get_template(template_id) → { info, source, theme }
// create_template(template_id, name, description, source, schema?) → TemplateInfo
// duplicate_template(template_id, new_id, new_name) → TemplateInfo
// delete_template(template_id) → string
// save_as_template(document_id, name, description?) → TemplateInfo
// create_document(name, template_id?) → DocumentState
// list_documents() → DocumentInfo[]
// save_document(document_id, name?) → DocumentInfo
// delete_document(document_id) → string
// get_workspace(document_id) → DocumentState
// get_source(document_id) → SourceResponse
// set_source(document_id, source) → DocumentState
// patch_source(document_id, find?, replace?, edits?, validate?) → PatchSourceResult
// get_theme(document_id) → { colors, fonts, spacing }
// set_theme(document_id, updates) → DocumentState
// import_content(base64_data, filename) → string
// get_voice() → string
// set_voice(content) → { status, path }
// get_components() → string
// set_components(source) → { status, path }
// list_assets() → string[]
// upload_asset(base64_data, filename) → { filename, path }
// delete_asset(filename) → { status, filename }
// list_fonts() → string[]
// install_font(url?, base64_data?, filename?) → { installed, count, fonts_dir }
// preview(document_id, page?) → ToolResult (resource_link to PDF)
// preview_template(template_id) → ToolResult
// export_pdf(document_id) → ToolResult
// compile_typst(source) → ToolResult
