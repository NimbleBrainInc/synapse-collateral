import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";
import type { DocumentInfo } from "../hooks/useDocuments";
import { PreviewPane } from "./PreviewPane";

interface DocumentsViewProps {
  documents: DocumentInfo[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  previewTitle: string;
  previewBlob: Blob | null;
  previewLoading: boolean;
  previewError: string;
}

export function DocumentsView({
  documents,
  selectedId,
  onSelect,
  onNew,
  onDelete,
  previewTitle,
  previewBlob,
  previewLoading,
  previewError,
}: DocumentsViewProps) {
  const { t } = useThemeTokens();

  return (
    <div style={s.mainLayout}>
      <div style={{ ...s.leftPanel, borderColor: t("border", "#e5e7eb") }}>
        <div style={s.listHeader}>
          <button
            style={{
              ...s.btn,
              ...s.btnPrimary,
              background: t("primary", "#2563eb"),
              width: "100%",
            }}
            onClick={onNew}
          >
            + New Document
          </button>
        </div>
        <div style={s.listScroll}>
          {documents.map((d) => (
            <div
              key={d.id}
              style={{
                ...s.listItem,
                borderColor: t("border", "#e5e7eb"),
                background:
                  selectedId === d.id ? t("secondary", "#f3f4f6") : "transparent",
              }}
              onClick={() => onSelect(d.id)}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{d.name}</div>
                <button
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "0.7rem",
                    color: t("muted", "#6b7280"),
                    padding: "0.2rem",
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(d.id);
                  }}
                  title="Delete"
                >
                  x
                </button>
              </div>
              <div
                style={{
                  fontSize: "0.7rem",
                  color: t("muted", "#6b7280"),
                  marginTop: "0.15rem",
                }}
              >
                {d.template_id || "custom"} &middot;{" "}
                {d.modified ? new Date(d.modified).toLocaleDateString() : ""}
              </div>
            </div>
          ))}
          {documents.length === 0 && (
            <div
              style={{
                padding: "1rem",
                fontSize: "0.82rem",
                color: t("muted", "#6b7280"),
                textAlign: "center",
              }}
            >
              No documents yet.
            </div>
          )}
        </div>
      </div>

      <PreviewPane
        title={previewTitle}
        blob={previewBlob}
        loading={previewLoading}
        error={previewError}
        hasSelection={!!selectedId}
        emptyHint="Select a document to preview"
      />
    </div>
  );
}
