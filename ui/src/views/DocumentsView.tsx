import { s, tokens } from "../styles";
import type { DocumentInfo } from "../hooks/useDocuments";
import { PreviewPane } from "./PreviewPane";

interface DocumentsViewProps {
  documents: DocumentInfo[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
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
  previewBlob,
  previewLoading,
  previewError,
}: DocumentsViewProps) {
  return (
    <div className="collateral-main-layout" style={s.mainLayout}>
      <div className="collateral-left-panel" style={s.leftPanel}>
        <div style={s.listHeader}>
          <button
            style={{ ...s.btn, ...s.btnPrimary, width: "100%" }}
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
                ...(selectedId === d.id ? s.listItemActive : {}),
              }}
              onClick={() => onSelect(d.id)}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <div style={{ ...s.listItemTitle, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {d.name}
                </div>
                <button
                  aria-label={`Delete ${d.name}`}
                  style={s.btnIcon}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(d.id);
                  }}
                  title="Delete"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <line x1="5" y1="5" x2="19" y2="19" />
                    <line x1="19" y1="5" x2="5" y2="19" />
                  </svg>
                </button>
              </div>
              <div style={s.listItemMeta}>
                {d.template_id || "custom"} ·{" "}
                {d.modified ? new Date(d.modified).toLocaleDateString() : ""}
              </div>
            </div>
          ))}
          {documents.length === 0 && (
            <div
              style={{
                padding: "1rem",
                fontSize: tokens.textSm,
                color: tokens.textSecondary,
                textAlign: "center",
              }}
            >
              No documents yet.
            </div>
          )}
        </div>
      </div>

      <PreviewPane
        blob={previewBlob}
        loading={previewLoading}
        error={previewError}
        hasSelection={!!selectedId}
        emptyHint="Select a document to preview"
      />
    </div>
  );
}
