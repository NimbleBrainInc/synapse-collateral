import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";
import type { TemplateInfo } from "../hooks/useTemplates";
import { PreviewPane } from "./PreviewPane";

interface TemplatesViewProps {
  templates: TemplateInfo[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDuplicate: (tpl: TemplateInfo) => void;
  onDelete: (id: string) => void;
  previewTitle: string;
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
  previewTitle,
  previewBlob,
  previewLoading,
  previewError,
}: TemplatesViewProps) {
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
            + New Template
          </button>
        </div>
        <div style={s.listScroll}>
          {templates.map((tpl) => (
            <div
              key={tpl.id}
              style={{
                ...s.listItem,
                borderColor: t("border", "#e5e7eb"),
                background:
                  selectedId === tpl.id ? t("secondary", "#f3f4f6") : "transparent",
              }}
              onClick={() => onSelect(tpl.id)}
            >
              <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{tpl.name}</div>
              {tpl.description && (
                <div
                  style={{
                    fontSize: "0.72rem",
                    color: t("muted", "#6b7280"),
                    marginTop: "0.15rem",
                  }}
                >
                  {tpl.description}
                </div>
              )}
              <div
                style={{
                  fontSize: "0.7rem",
                  color: t("muted", "#6b7280"),
                  marginTop: "0.15rem",
                }}
              >
                {tpl.page_count} page{tpl.page_count !== 1 ? "s" : ""}
              </div>
              <div
                style={{ display: "flex", gap: "0.25rem", marginTop: "0.35rem" }}
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  style={{ ...s.smallBtn, borderColor: t("border", "#e5e7eb") }}
                  onClick={() => onDuplicate(tpl)}
                >
                  Duplicate
                </button>
                <button
                  style={{
                    ...s.smallBtn,
                    borderColor: t("border", "#e5e7eb"),
                    color: t("destructive", "#ef4444"),
                  }}
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
                fontSize: "0.82rem",
                color: t("muted", "#6b7280"),
                textAlign: "center",
              }}
            >
              No templates yet.
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
        emptyHint="Select a template to preview"
      />
    </div>
  );
}
