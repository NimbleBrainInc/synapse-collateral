import { s } from "../styles";

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

const TAB_LABELS: Record<Tab, string> = {
  documents: "Documents",
  templates: "Templates",
};

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
  return (
    <nav className="collateral-topnav" style={s.nav}>
      <span className="collateral-logo" style={s.logo}>
        <span className="collateral-logo-full">Collateral Studio</span>
        <span className="collateral-logo-mark" aria-hidden="true">
          CS
        </span>
      </span>
      <div style={s.tabGroup} role="tablist" aria-label="Views">
        {(["documents", "templates"] as Tab[]).map((v) => {
          const active = tab === v;
          return (
            <button
              key={v}
              role="tab"
              aria-selected={active}
              onClick={() => onTabChange(v)}
              className={active ? "collateral-tab collateral-tab-active" : "collateral-tab"}
              style={{
                ...s.tabBtn,
                ...(active ? s.tabBtnActive : {}),
              }}
            >
              {TAB_LABELS[v]}
            </button>
          );
        })}
      </div>
      <div
        className="collateral-topnav-actions"
        style={{ marginLeft: "auto", display: "flex", gap: "0.4rem", alignItems: "center" }}
      >
        {selectedDocument && (
          <div className="collateral-doc-actions" style={{ display: "flex", gap: "0.4rem" }}>
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={onSave}
              disabled={saveStatus === "saving"}
            >
              {saveStatus === "saved" ? "Saved" : saveStatus === "saving" ? "Saving…" : "Save"}
            </button>
            <button
              className="collateral-doc-action-wide"
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={onSaveAsTemplate}
            >
              Save as Template
            </button>
            <button
              className="collateral-doc-action-wide"
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={onRename}
            >
              Rename
            </button>
          </div>
        )}
        <button
          aria-label="Settings"
          aria-pressed={settingsOpen}
          style={{
            ...s.btn,
            ...s.btnGhost,
            ...(settingsOpen
              ? { color: "var(--color-text-accent)", borderColor: "var(--color-text-accent)" }
              : {}),
          }}
          onClick={onToggleSettings}
        >
          Settings
        </button>
      </div>
    </nav>
  );
}
