import { useCallback, useEffect, useState } from "react";
import { useDataSync } from "@nimblebrain/synapse/react";
import { s } from "./styles";
import { useThemeTokens } from "./theme-utils";
import { injectResponsiveStyles } from "./styles/responsive";
import { TopNav } from "./components/TopNav";
import type { Tab, SaveStatus } from "./components/TopNav";
import { Dialog } from "./components/Dialog";
import { SettingsPanel } from "./components/SettingsPanel";
import { DocumentsView } from "./views/DocumentsView";
import { TemplatesView } from "./views/TemplatesView";
import { useDocuments } from "./hooks/useDocuments";
import type { TemplateInfo } from "./hooks/useTemplates";
import { useTemplates } from "./hooks/useTemplates";
import { usePreview } from "./hooks/usePreview";
import { useExport } from "./hooks/useExport";

type DialogType =
  | "newDoc"
  | "newTemplate"
  | "saveAsTemplate"
  | "deleteTemplate"
  | "renameDoc"
  | "deleteDoc"
  | null;

export function App() {
  const { t } = useThemeTokens();
  const [tab, setTab] = useState<Tab>("documents");

  const {
    documents,
    refresh: refreshDocs,
    create: createDoc,
    open: openDoc,
    save: saveDoc,
    remove: removeDoc,
    saveAsTemplate: saveDocAsTemplate,
  } = useDocuments();
  const {
    templates,
    refresh: refreshTemplates,
    create: createTemplate,
    duplicate: duplicateTemplate,
    remove: removeTemplate,
  } = useTemplates();
  const {
    blob: previewBlob,
    loading: previewLoading,
    error: previewError,
    previewDocument,
    previewTemplate,
    clear: clearPreview,
    setError: setPreviewError,
  } = usePreview();
  const { exportPdf } = useExport();

  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");

  const [settingsOpen, setSettingsOpen] = useState(false);

  const [dialogType, setDialogType] = useState<DialogType>(null);
  const [dialogName, setDialogName] = useState("");
  const [dialogDesc, setDialogDesc] = useState("");
  const [dialogTemplate, setDialogTemplate] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  useEffect(() => {
    injectResponsiveStyles();
  }, []);

  // Load list for the active tab when it changes.
  useEffect(() => {
    if (tab === "templates") refreshTemplates();
    else refreshDocs();
  }, [tab, refreshDocs, refreshTemplates]);

  // Auto-refresh when the agent changes data. Document previews refresh live;
  // template previews are static snapshots.
  useDataSync(() => {
    if (tab === "templates") refreshTemplates();
    if (tab === "documents") {
      refreshDocs();
      if (selectedDocument) previewDocument();
    }
  });

  const hasSelection = tab === "documents" ? !!selectedDocument : !!selectedTemplate;

  const previewTitle = (() => {
    if (tab === "templates" && selectedTemplate) {
      return templates.find((x) => x.id === selectedTemplate)?.name ?? selectedTemplate;
    }
    if (tab === "documents" && selectedDocument) {
      return documents.find((x) => x.id === selectedDocument)?.name ?? selectedDocument;
    }
    return "Preview";
  })();

  const handleSelectDocument = useCallback(
    async (id: string) => {
      setSelectedDocument(id);
      setSelectedTemplate(null);
      try {
        await openDoc(id);
        await previewDocument();
      } catch (e) {
        setPreviewError(e instanceof Error ? e.message : "Failed to open");
      }
    },
    [openDoc, previewDocument, setPreviewError],
  );

  const handleSelectTemplate = useCallback(
    async (id: string) => {
      setSelectedTemplate(id);
      setSelectedDocument(null);
      await previewTemplate(id);
    },
    [previewTemplate],
  );

  const openDialog = (type: "newDoc" | "newTemplate" | "saveAsTemplate") => {
    setDialogName("");
    setDialogDesc("");
    setDialogType(type);
  };

  const handleCreateDocument = async () => {
    const name = dialogName.trim();
    if (!name) return;
    try {
      const args: { name: string; template_id?: string } = { name };
      if (dialogTemplate) args.template_id = dialogTemplate;
      const ws = await createDoc(args);
      setDialogType(null);
      setSelectedDocument(ws.document_id);
      setSelectedTemplate(null);
      setDialogTemplate("");
      setTab("documents");
      await Promise.all([refreshDocs(), previewDocument()]);
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Failed to create document");
    }
  };

  const handleCreateTemplate = async () => {
    const name = dialogName.trim();
    if (!name) return;
    setDialogType(null);
    try {
      const tid = name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      await createTemplate({
        template_id: tid,
        name,
        description: dialogDesc.trim(),
        source: "",
      });
      await refreshTemplates();
    } catch {
      /* non-critical */
    }
  };

  const handleDuplicateTemplate = async (tpl: TemplateInfo) => {
    try {
      await duplicateTemplate({
        template_id: tpl.id,
        new_id: tpl.id + "-copy",
        new_name: tpl.name + " (Copy)",
      });
      await refreshTemplates();
    } catch {
      /* non-critical */
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    try {
      await removeTemplate(id);
      setDeleteConfirmId(null);
      setDialogType(null);
      if (selectedTemplate === id) {
        setSelectedTemplate(null);
        clearPreview();
      }
      await refreshTemplates();
    } catch {
      /* non-critical */
    }
  };

  const handleSaveDocument = async () => {
    setSaveStatus("saving");
    try {
      await saveDoc();
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 1500);
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Save failed");
      setSaveStatus("idle");
    }
  };

  const handleSaveAsTemplate = async () => {
    const name = dialogName.trim();
    if (!name) return;
    setDialogType(null);
    try {
      await saveDocAsTemplate({ name, description: dialogDesc.trim() });
      await refreshTemplates();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Failed to save as template");
    }
  };

  const handleExport = async () => {
    try {
      await exportPdf();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Export failed");
    }
  };

  const handleDeleteDocument = async (id: string) => {
    setDialogType(null);
    setDeleteConfirmId(null);
    try {
      await removeDoc(id);
      if (selectedDocument === id) {
        setSelectedDocument(null);
        clearPreview();
      }
      await refreshDocs();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleRenameDocument = async () => {
    const name = dialogName.trim();
    if (!name || !selectedDocument) return;
    setDialogType(null);
    try {
      await saveDoc({ name });
      await refreshDocs();
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "Rename failed");
    }
  };

  return (
    <div
      style={{
        ...s.root,
        background: t("background", "#fff"),
        color: t("foreground", "#1a1a1a"),
      }}
    >
      <TopNav
        tab={tab}
        onTabChange={setTab}
        selectedDocument={selectedDocument}
        saveStatus={saveStatus}
        onSave={handleSaveDocument}
        onSaveAsTemplate={() => openDialog("saveAsTemplate")}
        onExport={handleExport}
        onRename={() => {
          setDialogName("");
          setDialogType("renameDoc");
        }}
        settingsOpen={settingsOpen}
        onToggleSettings={() => setSettingsOpen((prev) => !prev)}
      />

      {tab === "documents" ? (
        <DocumentsView
          documents={documents}
          selectedId={selectedDocument}
          onSelect={handleSelectDocument}
          onNew={() => openDialog("newDoc")}
          onDelete={(id) => {
            setDeleteConfirmId(id);
            setDialogType("deleteDoc");
          }}
          previewTitle={previewTitle}
          previewBlob={previewBlob}
          previewLoading={previewLoading}
          previewError={hasSelection ? previewError : ""}
        />
      ) : (
        <TemplatesView
          templates={templates}
          selectedId={selectedTemplate}
          onSelect={handleSelectTemplate}
          onNew={() => openDialog("newTemplate")}
          onDuplicate={handleDuplicateTemplate}
          onDelete={(id) => {
            setDeleteConfirmId(id);
            setDialogType("deleteTemplate");
          }}
          previewTitle={previewTitle}
          previewBlob={previewBlob}
          previewLoading={previewLoading}
          previewError={hasSelection ? previewError : ""}
        />
      )}

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {dialogType === "newDoc" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>New Document</h3>
          <label style={s.label}>
            Name <span style={{ color: t("destructive", "#ef4444") }}>*</span>
          </label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && dialogName.trim() && handleCreateDocument()}
            placeholder="e.g. Acme Proposal Q2"
            autoFocus
            required
            style={{
              ...s.input,
              borderColor: t("border", "#e5e7eb"),
              background: t("card", "#f9fafb"),
            }}
          />
          <label style={{ ...s.label, marginTop: "0.75rem" }}>Template</label>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            <label
              style={{
                ...s.templateOpt,
                borderColor: !dialogTemplate
                  ? t("primary", "#2563eb")
                  : t("border", "#e5e7eb"),
                background: t("card", "#f9fafb"),
              }}
              onClick={() => setDialogTemplate("")}
            >
              <input
                type="radio"
                name="tpl"
                checked={!dialogTemplate}
                readOnly
                style={{ accentColor: t("primary", "#2563eb") }}
              />{" "}
              Blank document
            </label>
            {templates.map((tpl) => (
              <label
                key={tpl.id}
                style={{
                  ...s.templateOpt,
                  borderColor:
                    dialogTemplate === tpl.id
                      ? t("primary", "#2563eb")
                      : t("border", "#e5e7eb"),
                  background: t("card", "#f9fafb"),
                }}
                onClick={() => setDialogTemplate(tpl.id)}
              >
                <input
                  type="radio"
                  name="tpl"
                  checked={dialogTemplate === tpl.id}
                  readOnly
                  style={{ accentColor: t("primary", "#2563eb") }}
                />{" "}
                {tpl.name}
              </label>
            ))}
          </div>
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              justifyContent: "flex-end",
              marginTop: "1.25rem",
            }}
          >
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={() => setDialogType(null)}
            >
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
        </Dialog>
      )}

      {dialogType === "newTemplate" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>New Template</h3>
          <label style={s.label}>Name</label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreateTemplate()}
            placeholder="e.g. Weekly Report"
            autoFocus
            style={{
              ...s.input,
              borderColor: t("border", "#e5e7eb"),
              background: t("card", "#f9fafb"),
            }}
          />
          <label style={{ ...s.label, marginTop: "0.75rem" }}>Description</label>
          <input
            type="text"
            value={dialogDesc}
            onChange={(e) => setDialogDesc(e.target.value)}
            placeholder="Brief description"
            style={{
              ...s.input,
              borderColor: t("border", "#e5e7eb"),
              background: t("card", "#f9fafb"),
            }}
          />
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              justifyContent: "flex-end",
              marginTop: "1.25rem",
            }}
          >
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb") }}
              onClick={handleCreateTemplate}
            >
              Create
            </button>
          </div>
        </Dialog>
      )}

      {dialogType === "saveAsTemplate" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>Save as Template</h3>
          <label style={s.label}>Template Name</label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSaveAsTemplate()}
            placeholder="e.g. Quarterly Report"
            autoFocus
            style={{
              ...s.input,
              borderColor: t("border", "#e5e7eb"),
              background: t("card", "#f9fafb"),
            }}
          />
          <label style={{ ...s.label, marginTop: "0.75rem" }}>Description</label>
          <input
            type="text"
            value={dialogDesc}
            onChange={(e) => setDialogDesc(e.target.value)}
            placeholder="Brief description"
            style={{
              ...s.input,
              borderColor: t("border", "#e5e7eb"),
              background: t("card", "#f9fafb"),
            }}
          />
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              justifyContent: "flex-end",
              marginTop: "1.25rem",
            }}
          >
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary, background: t("primary", "#2563eb") }}
              onClick={handleSaveAsTemplate}
            >
              Save
            </button>
          </div>
        </Dialog>
      )}

      {dialogType === "deleteTemplate" && deleteConfirmId && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Delete Template</h3>
          <p
            style={{
              fontSize: "0.82rem",
              color: t("muted", "#6b7280"),
              marginBottom: "1rem",
            }}
          >
            Are you sure? This cannot be undone.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={() => {
                setDialogType(null);
                setDeleteConfirmId(null);
              }}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary, background: t("destructive", "#ef4444") }}
              onClick={() => handleDeleteTemplate(deleteConfirmId)}
            >
              Delete
            </button>
          </div>
        </Dialog>
      )}

      {dialogType === "renameDoc" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={{ fontSize: "1rem", marginBottom: "1rem" }}>Rename Document</h3>
          <label style={s.label}>New name</label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && dialogName.trim() && handleRenameDocument()}
            placeholder="Document name"
            autoFocus
            style={{
              ...s.input,
              borderColor: t("border", "#e5e7eb"),
              background: t("card", "#f9fafb"),
            }}
          />
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              justifyContent: "flex-end",
              marginTop: "1.25rem",
            }}
          >
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={() => setDialogType(null)}
            >
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
        </Dialog>
      )}

      {dialogType === "deleteDoc" && deleteConfirmId && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Delete Document</h3>
          <p
            style={{
              fontSize: "0.82rem",
              color: t("muted", "#6b7280"),
              marginBottom: "1rem",
            }}
          >
            Are you sure you want to delete this document? This cannot be undone.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary, background: t("destructive", "#ef4444") }}
              onClick={() => handleDeleteDocument(deleteConfirmId)}
            >
              Delete
            </button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
