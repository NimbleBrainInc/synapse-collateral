import { useCallback, useEffect, useState } from "react";
import { useDataSync } from "@nimblebrain/synapse/react";
import { s, tokens } from "./styles";
import { useInjectThemeTokens } from "./theme-utils";
import { injectResponsiveStyles } from "./styles/responsive";
import { TopNav } from "./components/TopNav";
import type { Tab } from "./components/TopNav";
import { Dialog } from "./components/Dialog";
import { SettingsPanel } from "./components/SettingsPanel";
import { DocumentsView } from "./views/DocumentsView";
import { TemplatesView } from "./views/TemplatesView";
import { AssetsView } from "./views/AssetsView";
import { useDocuments } from "./hooks/useDocuments";
import type { TemplateInfo } from "./hooks/useTemplates";
import { useTemplates } from "./hooks/useTemplates";
import { useAssets } from "./hooks/useAssets";
import { usePreview } from "./hooks/usePreview";

type DialogType =
  | "newDoc"
  | "newTemplate"
  | "saveAsTemplate"
  | "deleteTemplate"
  | "renameDoc"
  | "deleteDoc"
  | null;

export function App() {
  useInjectThemeTokens();
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
    assets,
    refresh: refreshAssets,
    upload: uploadAsset,
    remove: removeAsset,
  } = useAssets();
  const {
    blob: previewBlob,
    loading: previewLoading,
    error: previewError,
    previewDocument,
    previewTemplate,
    clear: clearPreview,
    setError: setPreviewError,
  } = usePreview();

  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [dialogType, setDialogType] = useState<DialogType>(null);
  const [dialogName, setDialogName] = useState("");
  const [dialogDesc, setDialogDesc] = useState("");
  const [dialogTemplate, setDialogTemplate] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  useEffect(() => {
    injectResponsiveStyles();
  }, []);

  useEffect(() => {
    if (tab === "templates") refreshTemplates();
    else if (tab === "assets") refreshAssets();
    else refreshDocs();
  }, [tab, refreshDocs, refreshTemplates, refreshAssets]);

  useDataSync(() => {
    if (tab === "templates") refreshTemplates();
    else if (tab === "assets") refreshAssets();
    else if (tab === "documents") {
      refreshDocs();
      if (selectedDocument) previewDocument();
    }
  });

  const hasSelection = tab === "documents" ? !!selectedDocument : !!selectedTemplate;

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
    <div className="collateral-root" style={s.root}>
      <TopNav
        tab={tab}
        onTabChange={setTab}
        selectedDocument={selectedDocument}
        onSaveAsTemplate={() => openDialog("saveAsTemplate")}
        onRename={() => {
          setDialogName("");
          setDialogType("renameDoc");
        }}
        settingsOpen={settingsOpen}
        onToggleSettings={() => setSettingsOpen((prev) => !prev)}
      />

      {tab === "documents" && (
        <DocumentsView
          documents={documents}
          selectedId={selectedDocument}
          onSelect={handleSelectDocument}
          onNew={() => openDialog("newDoc")}
          onDelete={(id) => {
            setDeleteConfirmId(id);
            setDialogType("deleteDoc");
          }}
          previewBlob={previewBlob}
          previewLoading={previewLoading}
          previewError={hasSelection ? previewError : ""}
        />
      )}
      {tab === "templates" && (
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
          previewBlob={previewBlob}
          previewLoading={previewLoading}
          previewError={hasSelection ? previewError : ""}
        />
      )}
      {tab === "assets" && (
        <AssetsView
          assets={assets}
          onUpload={uploadAsset}
          onDelete={removeAsset}
          onRefresh={refreshAssets}
        />
      )}

      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {dialogType === "newDoc" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={s.dialogTitle}>New Document</h3>
          <label style={s.label}>
            Name <span style={{ color: tokens.danger }}>*</span>
          </label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && dialogName.trim() && handleCreateDocument()}
            placeholder="e.g. Acme Proposal Q2"
            autoFocus
            required
            style={s.input}
          />
          <label style={{ ...s.label, marginTop: "0.75rem" }}>Template</label>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            <label
              style={{
                ...s.templateOpt,
                ...(!dialogTemplate ? s.templateOptActive : {}),
              }}
              onClick={() => setDialogTemplate("")}
            >
              <input
                type="radio"
                name="tpl"
                checked={!dialogTemplate}
                readOnly
                style={{ accentColor: tokens.textAccent }}
              />{" "}
              Blank document
            </label>
            {templates.map((tpl) => (
              <label
                key={tpl.id}
                style={{
                  ...s.templateOpt,
                  ...(dialogTemplate === tpl.id ? s.templateOptActive : {}),
                }}
                onClick={() => setDialogTemplate(tpl.id)}
              >
                <input
                  type="radio"
                  name="tpl"
                  checked={dialogTemplate === tpl.id}
                  readOnly
                  style={{ accentColor: tokens.textAccent }}
                />{" "}
                {tpl.name}
              </label>
            ))}
          </div>
          <div className="collateral-dialog-actions">
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary }}
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
          <h3 style={s.dialogTitle}>New Template</h3>
          <label style={s.label}>Name</label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreateTemplate()}
            placeholder="e.g. Weekly Report"
            autoFocus
            style={s.input}
          />
          <label style={{ ...s.label, marginTop: "0.75rem" }}>Description</label>
          <input
            type="text"
            value={dialogDesc}
            onChange={(e) => setDialogDesc(e.target.value)}
            placeholder="Brief description"
            style={s.input}
          />
          <div className="collateral-dialog-actions">
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary }}
              onClick={handleCreateTemplate}
            >
              Create
            </button>
          </div>
        </Dialog>
      )}

      {dialogType === "saveAsTemplate" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={s.dialogTitle}>Save as Template</h3>
          <label style={s.label}>Template Name</label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSaveAsTemplate()}
            placeholder="e.g. Quarterly Report"
            autoFocus
            style={s.input}
          />
          <label style={{ ...s.label, marginTop: "0.75rem" }}>Description</label>
          <input
            type="text"
            value={dialogDesc}
            onChange={(e) => setDialogDesc(e.target.value)}
            placeholder="Brief description"
            style={s.input}
          />
          <div className="collateral-dialog-actions">
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary }}
              onClick={handleSaveAsTemplate}
            >
              Save
            </button>
          </div>
        </Dialog>
      )}

      {dialogType === "deleteTemplate" && deleteConfirmId && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={s.dialogTitle}>Delete Template</h3>
          <p style={{ fontSize: tokens.textSm, color: tokens.textSecondary, margin: "0 0 1rem" }}>
            Are you sure? This cannot be undone.
          </p>
          <div className="collateral-dialog-actions">
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={() => {
                setDialogType(null);
                setDeleteConfirmId(null);
              }}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnDanger }}
              onClick={() => handleDeleteTemplate(deleteConfirmId)}
            >
              Delete
            </button>
          </div>
        </Dialog>
      )}

      {dialogType === "renameDoc" && (
        <Dialog onClose={() => setDialogType(null)}>
          <h3 style={s.dialogTitle}>Rename Document</h3>
          <label style={s.label}>New name</label>
          <input
            type="text"
            value={dialogName}
            onChange={(e) => setDialogName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && dialogName.trim() && handleRenameDocument()}
            placeholder="Document name"
            autoFocus
            style={s.input}
          />
          <div className="collateral-dialog-actions">
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnPrimary }}
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
          <h3 style={s.dialogTitle}>Delete Document</h3>
          <p style={{ fontSize: tokens.textSm, color: tokens.textSecondary, margin: "0 0 1rem" }}>
            Are you sure you want to delete this document? This cannot be undone.
          </p>
          <div className="collateral-dialog-actions">
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={() => setDialogType(null)}
            >
              Cancel
            </button>
            <button
              style={{ ...s.btn, ...s.btnDanger }}
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
