import { useState, useEffect, useCallback } from "react";
import {
  SynapseProvider,
  useCallTool,
  useDataSync,
  useSynapse,
  useTheme,
} from "@nimblebrain/synapse/react";

// --- Types matching server contracts ---

interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  page_count: number;
  variables: unknown[];
  created: string;
  modified: string;
}

interface DocumentInfo {
  id: string;
  name: string;
  template_id: string | null;
  created: string;
  modified: string;
}

interface WorkspaceState {
  document_id: string | null;
  document_name: string | null;
  template_id: string | null;
  theme: ThemeData;
  source: string;
  sections: unknown[];
  has_cache: boolean;
}

interface ThemeData {
  colors: Record<string, string>;
  fonts: Record<string, string>;
  spacing: Record<string, string>;
}

/**
 * Extract resource_link URIs from MCP tool content. The server returns
 * resource_link blocks per the MCP spec; bytes are fetched via
 * synapse.readResource over the ext-apps bridge.
 */
function extractResourceUris(blocks: unknown[]): string[] {
  return blocks
    .filter(
      (block): block is { type: "resource_link"; uri: string } =>
        block != null &&
        typeof block === "object" &&
        (block as Record<string, unknown>).type === "resource_link" &&
        typeof (block as Record<string, unknown>).uri === "string",
    )
    .map((block) => block.uri);
}

function base64ToBytes(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function fetchResourceAsBlob(
  synapse: ReturnType<typeof useSynapse>,
  uri: string,
): Promise<Blob> {
  const result = await synapse.readResource(uri);
  const first = result.contents[0];
  if (!first) throw new Error("No content returned for " + uri);
  const mimeType = first.mimeType ?? "application/octet-stream";
  if (first.blob !== undefined) {
    return new Blob([base64ToBytes(first.blob)], { type: mimeType });
  }
  if (first.text !== undefined) {
    return new Blob([first.text], { type: mimeType });
  }
  throw new Error("Resource has neither blob nor text: " + uri);
}

// --- Tab type ---
type Tab = "documents" | "templates";

// --- Settings sections ---
type SettingsSection = "voice" | "components" | "assets" | null;

function CollateralStudioUI() {
  const theme = useTheme();
  const synapse = useSynapse();
  const [tab, setTab] = useState<Tab>("documents");

  // Tool hooks
  const listTemplates = useCallTool<TemplateInfo[]>("list_templates");
  const createTemplateTool = useCallTool<TemplateInfo>("create_template");
  const duplicateTemplateTool = useCallTool<TemplateInfo>("duplicate_template");
  const deleteTemplateTool = useCallTool<string>("delete_template");
  const deleteDocumentTool = useCallTool<string>("delete_document");
  const createDocument = useCallTool<WorkspaceState>("create_document");
  const listDocuments = useCallTool<DocumentInfo[]>("list_documents");
  const openDocument = useCallTool<WorkspaceState>("open_document");
  const saveDocument = useCallTool<DocumentInfo>("save_document");
  const saveAsTemplate = useCallTool<TemplateInfo>("save_as_template");
  const previewTool = useCallTool("preview");
  const previewTemplateTool = useCallTool("preview_template");
  const exportPdf = useCallTool<ExportResult>("export_pdf");
  const uploadAsset = useCallTool<{ filename: string }>("upload_asset");
  const listAssetsTool = useCallTool<string[]>("list_assets");
  const deleteAssetTool = useCallTool<{ status: string }>("delete_asset");
  const setVoiceTool = useCallTool<{ status: string }>("set_voice");
  const getVoiceTool = useCallTool<string>("get_voice");
  const setComponentsTool = useCallTool<{ status: string }>("set_components");
  const getComponentsTool = useCallTool<string>("get_components");

  // List state
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);

  // Selection state
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);

  // Preview state
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);

  // Settings state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsSection, setSettingsSection] = useState<SettingsSection>(null);
  const [voice, setVoiceText] = useState("");
  const [components, setComponentsText] = useState("");
  const [assets, setAssets] = useState<string[]>([]);

  // Dialog state
  const [dialogType, setDialogType] = useState<"newDoc" | "newTemplate" | "saveAsTemplate" | "deleteTemplate" | "renameDoc" | "deleteDoc" | null>(null);
  const [dialogName, setDialogName] = useState("");
  const [dialogDesc, setDialogDesc] = useState("");
  const [dialogTemplate, setDialogTemplate] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const TOKEN_MAP: Record<string, string> = {
    background: "--color-background-primary",
    foreground: "--color-text-primary",
    card: "--color-background-secondary",
    primary: "--color-text-accent",
    border: "--color-border-primary",
    muted: "--color-text-secondary",
    secondary: "--color-background-secondary",
    destructive: "--nb-color-danger",
  };

  const t = (token: string, fallback: string) =>
    theme.tokens[TOKEN_MAP[token] ?? token] || fallback;

  // Whether we have an active document or template loaded for preview
  const hasSelection = tab === "documents" ? !!selectedDocument : !!selectedTemplate;

  const previewTitle = (() => {
    if (tab === "templates" && selectedTemplate) {
      return templates.find((x) => x.id === selectedTemplate)?.name ?? selectedTemplate;
    }
    if (tab === "documents" && selectedDocument) {
      return docs.find((x) => x.id === selectedDocument)?.name ?? selectedDocument;
    }
    return "Preview";
  })();
  const downloadFilename = `${previewTitle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "document"}.pdf`;

  // --- Data loading ---

  const loadTemplates = useCallback(async () => {
    try {
      const result = await listTemplates.call({});
      setTemplates((result.data as TemplateInfo[]) || []);
    } catch { /* non-critical */ }
  }, [listTemplates]);

  const loadDocs = useCallback(async () => {
    try {
      const result = await listDocuments.call({});
      setDocs((result.data as DocumentInfo[]) || []);
    } catch { /* non-critical */ }
  }, [listDocuments]);

  const loadSettings = useCallback(async () => {
    try {
      const [voiceResult, componentsResult, assetsResult] = await Promise.all([
        getVoiceTool.call({}),
        getComponentsTool.call({}),
        listAssetsTool.call({}),
      ]);
      setVoiceText((voiceResult.data as string) || "");
      setComponentsText((componentsResult.data as string) || "");
      setAssets((assetsResult.data as string[]) || []);
    } catch { /* non-critical */ }
  }, [getVoiceTool, getComponentsTool, listAssetsTool]);

  // Refresh the current document's preview (workspace-based).
  // Only used after openDocument — template previews use preview_template directly.
  const refreshPreview = useCallback(async () => {
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const result = await previewTool.call({});
      const [uri] = extractResourceUris(result.content ?? []);
      if (!uri) throw new Error("Preview returned no resource_link");
      const url = URL.createObjectURL(await fetchResourceAsBlob(synapse, uri));
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return url;
      });
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Preview failed");
    }
    setPreviewLoading(false);
  }, [previewTool]);

  // --- Open a document for preview ---
  const handleSelectDocument = useCallback(async (id: string) => {
    setSelectedDocument(id);
    setSelectedTemplate(null);
    try {
      await openDocument.call({ document_id: id });
      await refreshPreview();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Failed to open");
    }
  }, [openDocument, refreshPreview]);

  // --- Open a template for preview ---
  const handleSelectTemplate = useCallback(async (id: string) => {
    setSelectedTemplate(id);
    setSelectedDocument(null);
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const result = await previewTemplateTool.call({ template_id: id });
      const [uri] = extractResourceUris(result.content ?? []);
      if (!uri) throw new Error("Template preview returned no resource_link");
      const url = URL.createObjectURL(await fetchResourceAsBlob(synapse, uri));
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return url;
      });
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Failed to preview template");
    }
    setPreviewLoading(false);
  }, [previewTemplateTool]);

  // Auto-refresh when the agent calls tools (data-changed from host).
  // Only refresh the document preview — template previews are static snapshots
  // that don't change in response to agent activity.
  useDataSync(() => {
    if (tab === "templates") loadTemplates();
    if (tab === "documents") {
      loadDocs();
      if (selectedDocument) refreshPreview();
    }
  });

  // Load data when tab changes
  useEffect(() => {
    if (tab === "templates") loadTemplates();
    if (tab === "documents") loadDocs();
  }, [tab]);

  // --- Actions ---

  async function handleCreateDocument() {
    const name = dialogName.trim();
    if (!name) return;
    try {
      const args: Record<string, unknown> = { name };
      if (dialogTemplate) args.template_id = dialogTemplate;
      const result = await createDocument.call(args);
      const ws = result.data as WorkspaceState;
      setDialogType(null);
      setSelectedDocument(ws.document_id);
      setSelectedTemplate(null);
      setDialogTemplate("");
      setTab("documents");
      await Promise.all([loadDocs(), refreshPreview()]);
    } catch (e) {
      // Keep dialog open and show error
      setPreviewError(e instanceof Error ? e.message : "Failed to create document");
    }
  }

  async function handleCreateTemplate() {
    const name = dialogName.trim();
    if (!name) return;
    setDialogType(null);
    try {
      const tid = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
      await createTemplateTool.call({
        template_id: tid,
        name,
        description: dialogDesc.trim(),
        source: "",
      });
      await loadTemplates();
    } catch { /* non-critical */ }
  }

  async function handleDuplicateTemplate(tpl: TemplateInfo) {
    try {
      await duplicateTemplateTool.call({
        template_id: tpl.id,
        new_id: tpl.id + "-copy",
        new_name: tpl.name + " (Copy)",
      });
      await loadTemplates();
    } catch { /* non-critical */ }
  }

  async function handleDeleteTemplate(id: string) {
    try {
      await deleteTemplateTool.call({ template_id: id });
      setDeleteConfirmId(null);
      setDialogType(null);
      if (selectedTemplate === id) {
        setSelectedTemplate(null);
        setPreviewUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return null;
        });
      }
      await loadTemplates();
    } catch { /* non-critical */ }
  }

  async function handleSaveDocument() {
    setSaveStatus("saving");
    try {
      await saveDocument.call({});
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 1500);
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Save failed");
      setSaveStatus("idle");
    }
  }

  async function handleSaveAsTemplate() {
    const name = dialogName.trim();
    if (!name) return;
    setDialogType(null);
    try {
      await saveAsTemplate.call({ name, description: dialogDesc.trim() });
      await loadTemplates();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Failed to save as template");
    }
  }

  async function handleExport() {
    try {
      const result = await exportPdf.call({});
      const uris = extractResourceUris(result.content ?? []);
      const pdfUri = uris[0];
      if (!pdfUri) return;
      const blob = await fetchResourceAsBlob(synapse, pdfUri);
      const filename = pdfUri.split("/").pop() || "document.pdf";
      synapse.downloadFile(filename, blob, "application/pdf");
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Export failed");
    }
  }

  async function handleDeleteDocument(id: string) {
    setDialogType(null);
    setDeleteConfirmId(null);
    try {
      await deleteDocumentTool.call({ document_id: id });
      if (selectedDocument === id) {
        setSelectedDocument(null);
      }
      await loadDocs();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  async function handleRenameDocument() {
    const name = dialogName.trim();
    if (!name || !selectedDocument) return;
    setDialogType(null);
    try {
      await saveDocument.call({ name });
      await loadDocs();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Rename failed");
    }
  }

  function openDialog(type: "newDoc" | "newTemplate" | "saveAsTemplate") {
    setDialogName("");
    setDialogDesc("");
    setDialogType(type);
  }

  // --- Render ---

  return (
    <div style={{ ...s.root, background: t("background", "#fff"), color: t("foreground", "#1a1a1a") }}>
      <style>{PREVIEW_CSS}</style>
      {/* Top bar */}
      <nav style={{ ...s.nav, borderColor: t("border", "#e5e7eb") }}>
        <span style={s.logo}>Collateral Studio</span>
        <div style={s.tabGroup}>
          {(["documents", "templates"] as Tab[]).map((v) => (
            <button
              key={v}
              onClick={() => setTab(v)}
              style={{
                ...s.tabBtn,
                color: tab === v ? t("primary", "#2563eb") : t("muted", "#6b7280"),
                borderBottomColor: tab === v ? t("primary", "#2563eb") : "transparent",
              }}
            >
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: "0.35rem" }}>
          {selectedDocument && (
            <>
              <button
                style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
                onClick={handleSaveDocument}
                disabled={saveStatus === "saving"}
              >
                {saveStatus === "saved" ? "Saved!" : saveStatus === "saving" ? "Saving..." : "Save"}
              </button>
              <button
                style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
                onClick={() => openDialog("saveAsTemplate")}
              >
                Save as Template
              </button>
              <button
                style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
                onClick={handleExport}
              >
                Export PDF
              </button>
              <button
                style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
                onClick={() => { setDialogName(""); setDialogType("renameDoc"); }}
              >
                Rename
              </button>
            </>
          )}
          <button
            style={{
              ...s.btn,
              ...s.btnGhost,
              borderColor: t("border", "#e5e7eb"),
              color: settingsOpen ? t("primary", "#2563eb") : t("muted", "#6b7280"),
            }}
            onClick={() => {
              setSettingsOpen(!settingsOpen);
              if (!settingsOpen) loadSettings();
            }}
          >
            Settings
          </button>
        </div>
      </nav>

      {/* Main content */}
      <div style={s.mainLayout}>
        {/* Left panel: list */}
        <div style={{ ...s.leftPanel, borderColor: t("border", "#e5e7eb") }}>
          {/* Action buttons */}
          <div style={s.listHeader}>
            {tab === "templates" && (
              <button
                style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb"), width: "100%" }}
                onClick={() => openDialog("newTemplate")}
              >
                + New Template
              </button>
            )}
            {tab === "documents" && (
              <button
                style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb"), width: "100%" }}
                onClick={() => openDialog("newDoc")}
              >
                + New Document
              </button>
            )}
          </div>

          {/* List items */}
          <div style={s.listScroll}>
            {tab === "templates" && templates.map((tpl) => (
              <div
                key={tpl.id}
                style={{
                  ...s.listItem,
                  borderColor: t("border", "#e5e7eb"),
                  background: selectedTemplate === tpl.id ? t("secondary", "#f3f4f6") : "transparent",
                }}
                onClick={() => handleSelectTemplate(tpl.id)}
              >
                <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{tpl.name}</div>
                {tpl.description && (
                  <div style={{ fontSize: "0.72rem", color: t("muted", "#6b7280"), marginTop: "0.15rem" }}>
                    {tpl.description}
                  </div>
                )}
                <div style={{ fontSize: "0.7rem", color: t("muted", "#6b7280"), marginTop: "0.15rem" }}>
                  {tpl.page_count} page{tpl.page_count !== 1 ? "s" : ""}
                </div>
                <div style={{ display: "flex", gap: "0.25rem", marginTop: "0.35rem" }} onClick={(e) => e.stopPropagation()}>
                  <button
                    style={{ ...s.smallBtn, borderColor: t("border", "#e5e7eb") }}
                    onClick={() => handleDuplicateTemplate(tpl)}
                  >
                    Duplicate
                  </button>
                  <button
                    style={{ ...s.smallBtn, borderColor: t("border", "#e5e7eb"), color: t("destructive", "#ef4444") }}
                    onClick={() => { setDeleteConfirmId(tpl.id); setDialogType("deleteTemplate"); }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}

            {tab === "documents" && docs.map((d) => (
              <div
                key={d.id}
                style={{
                  ...s.listItem,
                  borderColor: t("border", "#e5e7eb"),
                  background: selectedDocument === d.id ? t("secondary", "#f3f4f6") : "transparent",
                }}
                onClick={() => handleSelectDocument(d.id)}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{d.name}</div>
                  <button
                    style={{ background: "none", border: "none", cursor: "pointer", fontSize: "0.7rem", color: t("muted", "#6b7280"), padding: "0.2rem" }}
                    onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(d.id); setDialogType("deleteDoc"); }}
                    title="Delete"
                  >
                    x
                  </button>
                </div>
                <div style={{ fontSize: "0.7rem", color: t("muted", "#6b7280"), marginTop: "0.15rem" }}>
                  {d.template_id || "custom"} &middot;{" "}
                  {d.modified ? new Date(d.modified).toLocaleDateString() : ""}
                </div>
              </div>
            ))}

            {tab === "templates" && templates.length === 0 && (
              <div style={{ padding: "1rem", fontSize: "0.82rem", color: t("muted", "#6b7280"), textAlign: "center" }}>
                No templates yet.
              </div>
            )}
            {tab === "documents" && docs.length === 0 && (
              <div style={{ padding: "1rem", fontSize: "0.82rem", color: t("muted", "#6b7280"), textAlign: "center" }}>
                No documents yet.
              </div>
            )}
          </div>
        </div>

        {/* Right panel: preview */}
        <div
          className="collateral-preview-pane"
          style={{ ...s.rightPanel, background: t("secondary", "#f3f4f6") }}
        >
          <div
            className="collateral-preview-frame"
            style={{
              ...s.previewFrame,
              background: t("background", "#ffffff"),
              borderColor: t("border", "#e5e7eb"),
            }}
          >
            <div
              style={{
                ...s.previewHeader,
                borderBottomColor: t("border", "#e5e7eb"),
                color: t("muted", "#6b7280"),
              }}
            >
              <div style={s.previewHeaderLabel}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M14 3v4a1 1 0 0 0 1 1h4" />
                  <path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z" />
                </svg>
                <span style={s.previewHeaderName}>
                  {previewTitle}
                </span>
              </div>
              {previewUrl && (
                <a
                  href={previewUrl}
                  download={downloadFilename}
                  aria-label="Download PDF"
                  style={{
                    ...s.previewDownload,
                    color: t("muted", "#6b7280"),
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M12 3v12" />
                    <path d="m7 10 5 5 5-5" />
                    <path d="M5 21h14" />
                  </svg>
                </a>
              )}
            </div>
            <div style={s.previewBody}>
              {previewUrl ? (
                <iframe
                  src={previewUrl}
                  title="Document preview"
                  style={s.previewIframe}
                />
              ) : (
                <div style={{ ...s.previewStatus, color: t("muted", "#6b7280") }}>
                  {previewError ? (
                    <span style={{ color: t("destructive", "#ef4444") }}>{previewError}</span>
                  ) : previewLoading ? (
                    <span className="collateral-preview-dots" aria-label="Rendering">
                      Rendering<span>.</span><span>.</span><span>.</span>
                    </span>
                  ) : !hasSelection ? (
                    <span>
                      Select a {tab === "templates" ? "template" : "document"} to preview
                    </span>
                  ) : null}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Settings panel (slide-over) */}
      {settingsOpen && (
        <div style={{ ...s.settingsOverlay }} onClick={(e) => e.target === e.currentTarget && setSettingsOpen(false)}>
          <div style={{ ...s.settingsPanel, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ fontSize: "1rem", fontWeight: 600 }}>Settings</h2>
              <button
                style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
                onClick={() => setSettingsOpen(false)}
              >
                Close
              </button>
            </div>

            {/* Settings nav */}
            <div style={{ display: "flex", gap: "0.35rem", marginBottom: "1rem" }}>
              {(["voice", "components", "assets"] as SettingsSection[]).map((sec) => (
                <button
                  key={sec!}
                  style={{
                    ...s.btn,
                    ...(settingsSection === sec ? s.btnPrimary : s.btnGhost),
                    background: settingsSection === sec ? t("primary", "#2563eb") : "transparent",
                    borderColor: t("border", "#e5e7eb"),
                  }}
                  onClick={() => setSettingsSection(settingsSection === sec ? null : sec)}
                >
                  {sec!.charAt(0).toUpperCase() + sec!.slice(1)}
                </button>
              ))}
            </div>

            {/* Voice */}
            {settingsSection === "voice" && (
              <div>
                <h4 style={s.sectionTitle}>Voice</h4>
                <p style={{ fontSize: "0.75rem", color: t("muted", "#6b7280"), marginBottom: "0.5rem" }}>
                  Brand voice, tone, and style guidance for the agent.
                </p>
                <textarea
                  value={voice}
                  onChange={(e) => setVoiceText(e.target.value)}
                  placeholder="Describe the brand voice, tone, and style..."
                  style={{ ...s.textarea, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
                />
                <button
                  style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb"), marginTop: "0.5rem" }}
                  onClick={async () => {
                    try { await setVoiceTool.call({ content: voice }); } catch { /* non-critical */ }
                  }}
                >
                  Save Voice
                </button>
              </div>
            )}

            {/* Components */}
            {settingsSection === "components" && (
              <div>
                <h4 style={s.sectionTitle}>Components</h4>
                <p style={{ fontSize: "0.75rem", color: t("muted", "#6b7280"), marginBottom: "0.5rem" }}>
                  Reusable Typst functions and imports.
                </p>
                <textarea
                  value={components}
                  onChange={(e) => setComponentsText(e.target.value)}
                  placeholder="Reusable Typst components (functions, imports, etc.)..."
                  style={{ ...s.textarea, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb"), fontFamily: "monospace" }}
                />
                <button
                  style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb"), marginTop: "0.5rem" }}
                  onClick={async () => {
                    try { await setComponentsTool.call({ source: components }); } catch { /* non-critical */ }
                  }}
                >
                  Save Components
                </button>
              </div>
            )}

            {/* Assets */}
            {settingsSection === "assets" && (
              <div>
                <h4 style={s.sectionTitle}>Assets</h4>
                <div style={s.assetGrid}>
                  {assets.map((filename) => (
                    <div key={filename} style={{ ...s.assetCard, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}>
                      <div style={{ ...s.assetThumb, background: t("secondary", "#f3f4f6"), display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.65rem", color: t("muted", "#6b7280") }}>
                        {filename.split(".").pop()?.toUpperCase() || "FILE"}
                      </div>
                      <div style={{ fontSize: "0.7rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 100 }}>{filename}</div>
                      <button
                        style={{ ...s.smallBtn, borderColor: t("border", "#e5e7eb"), color: t("destructive", "#ef4444"), marginTop: "0.25rem" }}
                        onClick={async () => {
                          try {
                            await deleteAssetTool.call({ filename });
                            setAssets((prev) => prev.filter((x) => x !== filename));
                          } catch { /* non-critical */ }
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                  <label style={{ ...s.assetCard, ...s.dashed, borderColor: t("border", "#e5e7eb"), cursor: "pointer" }}>
                    + Upload
                    <input
                      type="file"
                      style={{ display: "none" }}
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        const reader = new FileReader();
                        reader.onload = async () => {
                          const base64 = (reader.result as string).split(",")[1];
                          try {
                            await uploadAsset.call({ filename: file.name, base64_data: base64 });
                            await loadSettings();
                          } catch { /* non-critical */ }
                        };
                        reader.readAsDataURL(file);
                        e.target.value = "";
                      }}
                    />
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Dialogs */}
      {dialogType === "newDoc" && (
        <div style={s.overlay} onClick={(e) => e.target === e.currentTarget && setDialogType(null)}>
          <div style={{ ...s.dialog, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>New Document</h3>
            <label style={s.label}>Name <span style={{ color: t("destructive", "#ef4444") }}>*</span></label>
            <input
              type="text"
              value={dialogName}
              onChange={(e) => setDialogName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && dialogName.trim() && handleCreateDocument()}
              placeholder="e.g. Acme Proposal Q2"
              autoFocus
              required
              style={{ ...s.input, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
            />
            <label style={{ ...s.label, marginTop: "0.75rem" }}>Template</label>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <label
                style={{
                  ...s.templateOpt,
                  borderColor: !dialogTemplate ? t("primary", "#2563eb") : t("border", "#e5e7eb"),
                  background: t("card", "#f9fafb"),
                }}
                onClick={() => setDialogTemplate("")}
              >
                <input type="radio" name="tpl" checked={!dialogTemplate} readOnly style={{ accentColor: t("primary", "#2563eb") }} /> Blank document
              </label>
              {templates.map((tpl) => (
                <label
                  key={tpl.id}
                  style={{
                    ...s.templateOpt,
                    borderColor: dialogTemplate === tpl.id ? t("primary", "#2563eb") : t("border", "#e5e7eb"),
                    background: t("card", "#f9fafb"),
                  }}
                  onClick={() => setDialogTemplate(tpl.id)}
                >
                  <input type="radio" name="tpl" checked={dialogTemplate === tpl.id} readOnly style={{ accentColor: t("primary", "#2563eb") }} /> {tpl.name}
                </label>
              ))}
            </div>
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1.25rem" }}>
              <button style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }} onClick={() => setDialogType(null)}>
                Cancel
              </button>
              <button
                style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb") }}
                onClick={handleCreateDocument}
                disabled={!dialogName.trim()}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {dialogType === "newTemplate" && (
        <div style={s.overlay} onClick={(e) => e.target === e.currentTarget && setDialogType(null)}>
          <div style={{ ...s.dialog, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>New Template</h3>
            <label style={s.label}>Name</label>
            <input
              type="text"
              value={dialogName}
              onChange={(e) => setDialogName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateTemplate()}
              placeholder="e.g. Weekly Report"
              autoFocus
              style={{ ...s.input, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
            />
            <label style={{ ...s.label, marginTop: "0.75rem" }}>Description</label>
            <input
              type="text"
              value={dialogDesc}
              onChange={(e) => setDialogDesc(e.target.value)}
              placeholder="Brief description"
              style={{ ...s.input, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
            />
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1.25rem" }}>
              <button style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }} onClick={() => setDialogType(null)}>
                Cancel
              </button>
              <button style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb") }} onClick={handleCreateTemplate}>
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {dialogType === "saveAsTemplate" && (
        <div style={s.overlay} onClick={(e) => e.target === e.currentTarget && setDialogType(null)}>
          <div style={{ ...s.dialog, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>Save as Template</h3>
            <label style={s.label}>Template Name</label>
            <input
              type="text"
              value={dialogName}
              onChange={(e) => setDialogName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSaveAsTemplate()}
              placeholder="e.g. Quarterly Report"
              autoFocus
              style={{ ...s.input, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
            />
            <label style={{ ...s.label, marginTop: "0.75rem" }}>Description</label>
            <input
              type="text"
              value={dialogDesc}
              onChange={(e) => setDialogDesc(e.target.value)}
              placeholder="Brief description"
              style={{ ...s.input, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
            />
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1.25rem" }}>
              <button style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }} onClick={() => setDialogType(null)}>
                Cancel
              </button>
              <button style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb") }} onClick={handleSaveAsTemplate}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {dialogType === "deleteTemplate" && deleteConfirmId && (
        <div style={s.overlay} onClick={(e) => e.target === e.currentTarget && setDialogType(null)}>
          <div style={{ ...s.dialog, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Delete Template</h3>
            <p style={{ fontSize: "0.82rem", color: t("muted", "#6b7280"), marginBottom: "1rem" }}>
              Are you sure? This cannot be undone.
            </p>
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
              <button style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }} onClick={() => { setDialogType(null); setDeleteConfirmId(null); }}>
                Cancel
              </button>
              <button
                style={{ ...s.btn, ...s.btnPrimary, background: t("destructive", "#ef4444") }}
                onClick={() => handleDeleteTemplate(deleteConfirmId)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {dialogType === "renameDoc" && (
        <div style={s.overlay} onClick={(e) => e.target === e.currentTarget && setDialogType(null)}>
          <div style={{ ...s.dialog, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>Rename Document</h3>
            <label style={s.label}>New name</label>
            <input
              type="text"
              value={dialogName}
              onChange={(e) => setDialogName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && dialogName.trim() && handleRenameDocument()}
              placeholder="Document name"
              autoFocus
              style={{ ...s.input, borderColor: t("border", "#e5e7eb"), background: t("card", "#f9fafb") }}
            />
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "1.25rem" }}>
              <button style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }} onClick={() => setDialogType(null)}>
                Cancel
              </button>
              <button
                style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb") }}
                onClick={handleRenameDocument}
                disabled={!dialogName.trim()}
              >
                Rename
              </button>
            </div>
          </div>
        </div>
      )}

      {dialogType === "deleteDoc" && deleteConfirmId && (
        <div style={s.overlay} onClick={(e) => e.target === e.currentTarget && setDialogType(null)}>
          <div style={{ ...s.dialog, background: t("background", "#fff"), borderColor: t("border", "#e5e7eb") }}>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Delete Document</h3>
            <p style={{ fontSize: "0.82rem", color: t("muted", "#6b7280"), marginBottom: "1rem" }}>
              Are you sure you want to delete this document? This cannot be undone.
            </p>
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
              <button style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }} onClick={() => setDialogType(null)}>
                Cancel
              </button>
              <button
                style={{ ...s.btn, ...s.btnPrimary, background: t("destructive", "#ef4444") }}
                onClick={() => handleDeleteDocument(deleteConfirmId)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function App() {
  return (
    <SynapseProvider name="collateral" version="0.1.0">
      <CollateralStudioUI />
    </SynapseProvider>
  );
}

// --- Styles ---

const s: Record<string, React.CSSProperties> = {
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    overflow: "hidden",
    fontFamily: "var(--font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif)",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    borderBottom: "1px solid",
    padding: "0 1rem",
    height: 44,
    flexShrink: 0,
    gap: "0.5rem",
  },
  logo: {
    fontWeight: 600,
    fontSize: "0.85rem",
    marginRight: "0.5rem",
  },
  tabGroup: {
    display: "flex",
    gap: 0,
  },
  tabBtn: {
    padding: "0.5rem 0.75rem",
    fontSize: "0.8rem",
    background: "none",
    border: "none",
    borderBottom: "2px solid",
    cursor: "pointer",
    lineHeight: "28px",
    fontFamily: "inherit",
  },
  mainLayout: {
    flex: 1,
    display: "flex",
    overflow: "hidden",
  },
  leftPanel: {
    width: 280,
    minWidth: 220,
    maxWidth: 360,
    borderRight: "1px solid",
    display: "flex",
    flexDirection: "column" as const,
    flexShrink: 0,
  },
  listHeader: {
    padding: "0.75rem",
    flexShrink: 0,
  },
  listScroll: {
    flex: 1,
    overflowY: "auto" as const,
  },
  listItem: {
    padding: "0.65rem 0.75rem",
    borderBottom: "1px solid",
    cursor: "pointer",
    transition: "background 0.1s",
  },
  rightPanel: {
    flex: 1,
    minWidth: 0,
    display: "flex",
    flexDirection: "column" as const,
    padding: "clamp(0rem, 2.5vw, 1.25rem)",
    overflow: "hidden",
  },
  previewFrame: {
    flex: 1,
    minHeight: 0,
    display: "flex",
    flexDirection: "column" as const,
    border: "1px solid",
    borderRadius: 10,
    overflow: "hidden",
    boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06)",
  },
  previewHeader: {
    height: 36,
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 0.75rem",
    borderBottom: "1px solid",
    fontSize: "0.72rem",
    letterSpacing: "0.01em",
  },
  previewHeaderLabel: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    minWidth: 0,
    flex: 1,
  },
  previewHeaderName: {
    whiteSpace: "nowrap" as const,
    overflow: "hidden",
    textOverflow: "ellipsis",
    fontWeight: 500,
    fontSize: "0.76rem",
    letterSpacing: "0",
  },
  previewDownload: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 28,
    height: 28,
    borderRadius: 6,
    textDecoration: "none",
    flexShrink: 0,
    transition: "background 120ms ease, color 120ms ease",
  },
  previewBody: {
    flex: 1,
    minHeight: 0,
    display: "flex",
    flexDirection: "column" as const,
  },
  previewIframe: {
    flex: 1,
    width: "100%",
    minHeight: 0,
    border: 0,
    display: "block",
    background: "transparent",
  },
  previewStatus: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "0.82rem",
    padding: "1.5rem",
    textAlign: "center" as const,
  },
  // Settings panel
  settingsOverlay: {
    position: "fixed" as const,
    inset: 0,
    background: "rgba(0,0,0,0.3)",
    zIndex: 90,
    display: "flex",
    justifyContent: "flex-end",
  },
  settingsPanel: {
    width: 400,
    maxWidth: "90vw",
    height: "100%",
    borderLeft: "1px solid",
    padding: "1.5rem",
    overflowY: "auto" as const,
    boxShadow: "-4px 0 20px rgba(0,0,0,0.1)",
  },
  sectionTitle: {
    fontSize: "0.7rem",
    textTransform: "uppercase" as const,
    letterSpacing: "1px",
    fontWeight: 600,
    margin: "0.5rem 0",
  },
  textarea: {
    width: "100%",
    padding: "0.5rem 0.6rem",
    borderRadius: 6,
    border: "1px solid",
    fontSize: "0.8rem",
    fontFamily: "inherit",
    outline: "none",
    minHeight: 140,
    resize: "vertical" as const,
  },
  assetGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))",
    gap: "0.5rem",
  },
  assetCard: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    padding: "0.5rem",
    borderRadius: 8,
    border: "1px solid",
    gap: "0.25rem",
  },
  assetThumb: {
    width: 56,
    height: 56,
    borderRadius: 4,
  },
  dashed: {
    border: "2px dashed",
    justifyContent: "center",
    minHeight: 80,
    fontSize: "0.82rem",
  },
  // Shared
  overlay: {
    position: "fixed" as const,
    inset: 0,
    background: "rgba(0,0,0,0.4)",
    zIndex: 100,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  dialog: {
    border: "1px solid",
    borderRadius: 12,
    padding: "1.5rem",
    width: 360,
    maxWidth: "90vw",
    boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
  },
  templateOpt: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    padding: "0.45rem 0.6rem",
    border: "1px solid",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: "0.8rem",
  },
  label: {
    display: "block",
    fontSize: "0.75rem",
    marginBottom: "0.2rem",
  },
  input: {
    width: "100%",
    padding: "0.45rem 0.6rem",
    borderRadius: 6,
    border: "1px solid",
    fontSize: "0.8rem",
    fontFamily: "inherit",
    outline: "none",
  },
  btn: {
    padding: "0.4rem 0.85rem",
    borderRadius: 6,
    border: "none",
    fontSize: "0.78rem",
    cursor: "pointer",
    fontWeight: 500,
    whiteSpace: "nowrap" as const,
    fontFamily: "inherit",
  },
  btnPrimary: {
    color: "#fff",
  },
  btnGhost: {
    background: "none",
    border: "1px solid",
  },
  smallBtn: {
    padding: "0.15rem 0.4rem",
    borderRadius: 4,
    border: "1px solid",
    fontSize: "0.68rem",
    cursor: "pointer",
    background: "none",
    fontFamily: "inherit",
  },
};

const PREVIEW_CSS = `
.collateral-preview-pane .collateral-preview-frame { transition: box-shadow 180ms ease, border-color 180ms ease; }
.collateral-preview-pane a[aria-label="Download PDF"]:hover { background: rgba(15, 23, 42, 0.06); color: inherit; }
.collateral-preview-pane a[aria-label="Download PDF"]:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
.collateral-preview-dots span { display: inline-block; opacity: 0; animation: collateral-dot 1.4s infinite; }
.collateral-preview-dots span:nth-child(2) { animation-delay: 0.2s; }
.collateral-preview-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes collateral-dot { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
@media (max-width: 640px) {
  .collateral-preview-pane { padding: 0 !important; }
  .collateral-preview-pane .collateral-preview-frame { border-radius: 0; border-left: 0; border-right: 0; box-shadow: none; }
}
@media (prefers-color-scheme: dark) {
  .collateral-preview-pane a[aria-label="Download PDF"]:hover { background: rgba(255, 255, 255, 0.08); }
}
`;
