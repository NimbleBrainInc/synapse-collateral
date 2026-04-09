// Auto-generated from Pydantic models — do not edit manually.
// Run: uv run python scripts/gen-types.py > ui/src/types.ts

export interface ThemeData {
  colors?: dict[str, str];
  fonts?: dict[str, str];
  spacing?: dict[str, str];
}

export interface VariableDefinition {
  name: string;
  type: string;
  description?: string;
  default?: unknown;
  required?: boolean;
  group?: string;
}

export interface TemplateInfo {
  id: string;
  name: string;
  description?: string;
  page_count?: number;
  variables?: VariableDefinition[];
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

export interface SectionState {
  name: string;
  type: string;
  group: string;
  value: unknown;
  required?: boolean;
  description?: string;
}

export interface WorkspaceState {
  document_id: string | null;
  document_name: string | null;
  template_id: string | null;
  theme?: ThemeData;
  source?: string;
  sections?: SectionState[];
  has_cache?: boolean;
}

export interface PagePreview {
  page_number: number;
  image_base64: string | null;
}

export interface PreviewResult {
  pages?: PagePreview[];
  page_count?: number;
  message?: string;
}

export interface ExportResult {
  pdf_base64: string | null;
  filename?: string;
  page_count?: number;
  size_bytes?: number;
  message?: string;
}

// --- Tool Return Type Reference ---
// list_templates() → TemplateInfo[]
// create_template() → TemplateInfo
// duplicate_template() → TemplateInfo
// save_as_template() → TemplateInfo
// create_document() → WorkspaceState
// list_documents() → DocumentInfo[]
// open_document() → WorkspaceState
// save_document() → DocumentInfo
// get_workspace() → WorkspaceState
// set_content() → WorkspaceState
// set_source() → WorkspaceState
// get_theme() → { colors: Record<string,string>, fonts: Record<string,string>, spacing: Record<string,string> }
// set_theme() → WorkspaceState
// get_template() → { info: TemplateInfo, source: string, theme: ThemeData }
// get_voice() → string
// set_voice() → { status: string; path: string }
// list_assets() → string[]
// upload_asset() → { filename: string; path: string }
// delete_asset() → { status: string; filename: string }
// get_components() → string
// set_components() → { status: string; path: string }
// list_fonts() → string[]
// install_font() → { installed: string[]; count: number; fonts_dir: string }
// preview() → PreviewResult
// export_pdf() → ExportResult
// compile_typst() → ExportResult
