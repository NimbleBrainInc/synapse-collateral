import { useEffect, useRef, useState } from "react";
import { s } from "../styles";

export type Tab = "documents" | "templates" | "assets";

interface TopNavProps {
  tab: Tab;
  onTabChange: (tab: Tab) => void;
  selectedDocument: string | null;
  onSaveAsTemplate: () => void;
  onRename: () => void;
  settingsOpen: boolean;
  onToggleSettings: () => void;
}

const TAB_LABELS: Record<Tab, string> = {
  documents: "Documents",
  templates: "Templates",
  assets: "Assets",
};

export function TopNav({
  tab,
  onTabChange,
  selectedDocument,
  onSaveAsTemplate,
  onRename,
  settingsOpen,
  onToggleSettings,
}: TopNavProps) {
  const [overflowOpen, setOverflowOpen] = useState(false);
  const overflowRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!overflowOpen) return;
    const close = (e: MouseEvent) => {
      if (overflowRef.current && !overflowRef.current.contains(e.target as Node)) {
        setOverflowOpen(false);
      }
    };
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOverflowOpen(false);
    };
    window.addEventListener("mousedown", close);
    window.addEventListener("keydown", esc);
    return () => {
      window.removeEventListener("mousedown", close);
      window.removeEventListener("keydown", esc);
    };
  }, [overflowOpen]);

  return (
    <nav className="collateral-topnav" style={s.nav}>
      <span className="collateral-logo" style={s.logo}>
        <span className="collateral-logo-full">Collateral Studio</span>
        <span className="collateral-logo-mark" aria-hidden="true">
          CS
        </span>
      </span>
      <div style={s.tabGroup} role="tablist" aria-label="Views">
        {(["documents", "templates", "assets"] as Tab[]).map((v) => {
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
        style={{
          marginLeft: "auto",
          display: "flex",
          gap: "0.4rem",
          alignItems: "center",
          position: "relative",
        }}
      >
        {selectedDocument && (
          <div className="collateral-doc-actions" style={{ display: "flex", gap: "0.4rem" }}>
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={onSaveAsTemplate}
            >
              Save as Template
            </button>
            <button
              style={{ ...s.btn, ...s.btnGhost }}
              onClick={onRename}
            >
              Rename
            </button>
          </div>
        )}
        {selectedDocument && (
          <div className="collateral-overflow-btn" ref={overflowRef} style={{ position: "relative" }}>
            <button
              aria-label="Document actions"
              aria-haspopup="menu"
              aria-expanded={overflowOpen}
              style={{ ...s.btn, ...s.btnGhost, padding: "0 0.6rem" }}
              onClick={() => setOverflowOpen((v) => !v)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <circle cx="12" cy="5" r="1.6" />
                <circle cx="12" cy="12" r="1.6" />
                <circle cx="12" cy="19" r="1.6" />
              </svg>
            </button>
            {overflowOpen && (
              <div role="menu" className="collateral-overflow-menu">
                <button
                  role="menuitem"
                  onClick={() => {
                    setOverflowOpen(false);
                    onSaveAsTemplate();
                  }}
                >
                  Save as Template
                </button>
                <button
                  role="menuitem"
                  onClick={() => {
                    setOverflowOpen(false);
                    onRename();
                  }}
                >
                  Rename
                </button>
              </div>
            )}
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
