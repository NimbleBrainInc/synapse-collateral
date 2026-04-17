import { s, tokens } from "../styles";
import type { TemplateInfo } from "../hooks/useTemplates";
import { PreviewPane } from "./PreviewPane";

interface TemplatesViewProps {
  templates: TemplateInfo[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDuplicate: (tpl: TemplateInfo) => void;
  onDelete: (id: string) => void;
  previewBlob: Blob | null;
  previewLoading: boolean;
  previewError: string;
}

export function TemplatesView({
  templates,
  selectedId,
  onSelect,
  onNew,
  onDuplicate,
  onDelete,
  previewBlob,
  previewLoading,
  previewError,
}: TemplatesViewProps) {
  return (
    <div className="collateral-main-layout" style={s.mainLayout}>
      <div className="collateral-left-panel" style={s.leftPanel}>
        <div style={s.listHeader}>
          <button
            style={{ ...s.btn, ...s.btnPrimary, width: "100%" }}
            onClick={onNew}
          >
            + New Template
          </button>
        </div>
        <div style={s.listScroll}>
          {templates.map((tpl) => (
            <div
              key={tpl.id}
              style={{
                ...s.listItem,
                ...(selectedId === tpl.id ? s.listItemActive : {}),
              }}
              onClick={() => onSelect(tpl.id)}
            >
              <div style={s.listItemTitle}>{tpl.name}</div>
              {tpl.description && (
                <div style={s.listItemMeta}>{tpl.description}</div>
              )}
              <div style={s.listItemMeta}>
                {tpl.page_count} page{tpl.page_count !== 1 ? "s" : ""}
              </div>
              <div
                style={{ display: "flex", gap: "0.35rem", marginTop: "0.5rem" }}
                onClick={(e) => e.stopPropagation()}
              >
                <button style={s.smallBtn} onClick={() => onDuplicate(tpl)}>
                  Duplicate
                </button>
                <button
                  style={{ ...s.smallBtn, color: tokens.danger }}
                  onClick={() => onDelete(tpl.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
          {templates.length === 0 && (
            <div
              style={{
                padding: "1rem",
                fontSize: tokens.textSm,
                color: tokens.textSecondary,
                textAlign: "center",
              }}
            >
              No templates yet.
            </div>
          )}
        </div>
      </div>

      <PreviewPane
        blob={previewBlob}
        loading={previewLoading}
        error={previewError}
        hasSelection={!!selectedId}
        emptyHint="Select a template to preview"
      />
    </div>
  );
}
