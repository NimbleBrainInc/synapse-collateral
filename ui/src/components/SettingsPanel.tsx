import { useEffect, useState } from "react";
import { s, tokens } from "../styles";
import { useAssets } from "../hooks/useAssets";
import { useBrand } from "../hooks/useBrand";

type SettingsSection = "voice" | "components" | "assets" | null;

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const { assets, refresh: refreshAssets, upload, remove: removeAsset } = useAssets();
  const {
    voice,
    setVoice,
    components,
    setComponents,
    refresh: refreshBrand,
    saveVoice,
    saveComponents,
  } = useBrand();

  const [section, setSection] = useState<SettingsSection>("voice");

  useEffect(() => {
    if (open) {
      refreshBrand();
      refreshAssets();
    }
  }, [open, refreshBrand, refreshAssets]);

  if (!open) return null;

  return (
    <div
      style={s.settingsOverlay}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="collateral-settings-panel" style={s.settingsPanel}>
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          <h2
            style={{
              fontFamily: tokens.fontHeading,
              fontSize: tokens.headingSm,
              lineHeight: tokens.headingSmLh,
              fontWeight: tokens.weightSemibold,
              margin: 0,
              letterSpacing: "-0.01em",
            }}
          >
            Settings
          </h2>
          <button style={{ ...s.btn, ...s.btnGhost }} onClick={onClose}>
            Close
          </button>
        </header>

        <div
          role="tablist"
          aria-label="Settings sections"
          style={{ display: "flex", gap: "0.35rem", marginBottom: "1rem", flexWrap: "wrap" }}
        >
          {(["voice", "components", "assets"] as const).map((sec) => {
            const active = section === sec;
            return (
              <button
                key={sec}
                role="tab"
                aria-selected={active}
                style={{
                  ...s.btn,
                  ...(active ? s.btnPrimary : s.btnGhost),
                }}
                onClick={() => setSection(active ? null : sec)}
              >
                {sec.charAt(0).toUpperCase() + sec.slice(1)}
              </button>
            );
          })}
        </div>

        {section === "voice" && (
          <div>
            <h4 style={s.sectionTitle}>Voice</h4>
            <p style={{ fontSize: tokens.textSm, color: tokens.textSecondary, margin: "0 0 0.5rem" }}>
              Brand voice, tone, and style guidance for the agent.
            </p>
            <textarea
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              placeholder="Describe the brand voice, tone, and style…"
              style={s.textarea}
            />
            <div style={{ marginTop: "0.5rem" }}>
              <button
                style={{ ...s.btn, ...s.btnPrimary }}
                onClick={async () => {
                  try {
                    await saveVoice(voice);
                  } catch {
                    /* non-critical */
                  }
                }}
              >
                Save Voice
              </button>
            </div>
          </div>
        )}

        {section === "components" && (
          <div>
            <h4 style={s.sectionTitle}>Components</h4>
            <p style={{ fontSize: tokens.textSm, color: tokens.textSecondary, margin: "0 0 0.5rem" }}>
              Reusable Typst functions and imports.
            </p>
            <textarea
              value={components}
              onChange={(e) => setComponents(e.target.value)}
              placeholder="Reusable Typst components (functions, imports, etc.)…"
              style={{ ...s.textarea, fontFamily: tokens.fontMono }}
            />
            <div style={{ marginTop: "0.5rem" }}>
              <button
                style={{ ...s.btn, ...s.btnPrimary }}
                onClick={async () => {
                  try {
                    await saveComponents(components);
                  } catch {
                    /* non-critical */
                  }
                }}
              >
                Save Components
              </button>
            </div>
          </div>
        )}

        {section === "assets" && (
          <div>
            <h4 style={s.sectionTitle}>Assets</h4>
            <div style={s.assetGrid}>
              {assets.map((filename) => (
                <div key={filename} style={s.assetCard}>
                  <div style={s.assetThumb}>
                    {filename.split(".").pop()?.toUpperCase() || "FILE"}
                  </div>
                  <div
                    style={{
                      fontSize: tokens.textXs,
                      lineHeight: tokens.textXsLh,
                      color: tokens.textPrimary,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      maxWidth: "100%",
                      textAlign: "center",
                    }}
                    title={filename}
                  >
                    {filename}
                  </div>
                  <button
                    style={{ ...s.smallBtn, color: tokens.danger }}
                    onClick={async () => {
                      try {
                        await removeAsset(filename);
                      } catch {
                        /* non-critical */
                      }
                    }}
                  >
                    Delete
                  </button>
                </div>
              ))}
              <label style={{ ...s.assetCard, ...s.dashed, cursor: "pointer" }}>
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
                        await upload({ filename: file.name, base64_data: base64 });
                        await refreshAssets();
                      } catch {
                        /* non-critical */
                      }
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
  );
}
