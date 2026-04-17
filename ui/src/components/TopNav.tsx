import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";

export type Tab = "documents" | "templates";
export type SaveStatus = "idle" | "saving" | "saved";

interface TopNavProps {
  tab: Tab;
  onTabChange: (tab: Tab) => void;
  selectedDocument: string | null;
  saveStatus: SaveStatus;
  onSave: () => void;
  onSaveAsTemplate: () => void;
  onRename: () => void;
  settingsOpen: boolean;
  onToggleSettings: () => void;
}

export function TopNav({
  tab,
  onTabChange,
  selectedDocument,
  saveStatus,
  onSave,
  onSaveAsTemplate,
  onRename,
  settingsOpen,
  onToggleSettings,
}: TopNavProps) {
  const { t } = useThemeTokens();

  return (
    <nav style={{ ...s.nav, borderColor: t("border", "#e5e7eb") }}>
      <span style={s.logo}>Collateral Studio</span>
      <div style={s.tabGroup}>
        {(["documents", "templates"] as Tab[]).map((v) => (
          <button
            key={v}
            onClick={() => onTabChange(v)}
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
              onClick={onSave}
              disabled={saveStatus === "saving"}
            >
              {saveStatus === "saved" ? "Saved!" : saveStatus === "saving" ? "Saving..." : "Save"}
            </button>
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={onSaveAsTemplate}
            >
              Save as Template
            </button>
            <button
              style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
              onClick={onRename}
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
          onClick={onToggleSettings}
        >
          Settings
        </button>
      </div>
    </nav>
  );
}
