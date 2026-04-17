import { useEffect, useState } from "react";
import { s } from "../styles";
import { useThemeTokens } from "../theme-utils";
import { useAssets } from "../hooks/useAssets";
import { useBrand } from "../hooks/useBrand";

type SettingsSection = "voice" | "components" | "assets" | null;

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const { t } = useThemeTokens();
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

  const [section, setSection] = useState<SettingsSection>(null);

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
      <div
        style={{
          ...s.settingsPanel,
          background: t("background", "#fff"),
          borderColor: t("border", "#e5e7eb"),
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          <h2 style={{ fontSize: "1rem", fontWeight: 600 }}>Settings</h2>
          <button
            style={{ ...s.btn, ...s.btnGhost, borderColor: t("border", "#e5e7eb") }}
            onClick={onClose}
          >
            Close
          </button>
        </div>

        <div style={{ display: "flex", gap: "0.35rem", marginBottom: "1rem" }}>
          {(["voice", "components", "assets"] as const).map((sec) => (
            <button
              key={sec}
              style={{
                ...s.btn,
                ...(section === sec ? s.btnPrimary : s.btnGhost),
                background: section === sec ? t("primary", "#2563eb") : "transparent",
                borderColor: t("border", "#e5e7eb"),
              }}
              onClick={() => setSection(section === sec ? null : sec)}
            >
              {sec.charAt(0).toUpperCase() + sec.slice(1)}
            </button>
          ))}
        </div>

        {section === "voice" && (
          <div>
            <h4 style={s.sectionTitle}>Voice</h4>
            <p
              style={{
                fontSize: "0.75rem",
                color: t("muted", "#6b7280"),
                marginBottom: "0.5rem",
              }}
            >
              Brand voice, tone, and style guidance for the agent.
            </p>
            <textarea
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              placeholder="Describe the brand voice, tone, and style..."
              style={{
                ...s.textarea,
                borderColor: t("border", "#e5e7eb"),
                background: t("card", "#f9fafb"),
              }}
            />
            <button
              style={{
                ...s.btn,
                ...s.btnPrimary,
                background: t("primary", "#2563eb"),
                marginTop: "0.5rem",
              }}
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
        )}

        {section === "components" && (
          <div>
            <h4 style={s.sectionTitle}>Components</h4>
            <p
              style={{
                fontSize: "0.75rem",
                color: t("muted", "#6b7280"),
                marginBottom: "0.5rem",
              }}
            >
              Reusable Typst functions and imports.
            </p>
            <textarea
              value={components}
              onChange={(e) => setComponents(e.target.value)}
              placeholder="Reusable Typst components (functions, imports, etc.)..."
              style={{
                ...s.textarea,
                borderColor: t("border", "#e5e7eb"),
                background: t("card", "#f9fafb"),
                fontFamily: "monospace",
              }}
            />
            <button
              style={{
                ...s.btn,
                ...s.btnPrimary,
                background: t("primary", "#2563eb"),
                marginTop: "0.5rem",
              }}
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
        )}

        {section === "assets" && (
          <div>
            <h4 style={s.sectionTitle}>Assets</h4>
            <div style={s.assetGrid}>
              {assets.map((filename) => (
                <div
                  key={filename}
                  style={{
                    ...s.assetCard,
                    borderColor: t("border", "#e5e7eb"),
                    background: t("card", "#f9fafb"),
                  }}
                >
                  <div
                    style={{
                      ...s.assetThumb,
                      background: t("secondary", "#f3f4f6"),
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "0.65rem",
                      color: t("muted", "#6b7280"),
                    }}
                  >
                    {filename.split(".").pop()?.toUpperCase() || "FILE"}
                  </div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      maxWidth: 100,
                    }}
                  >
                    {filename}
                  </div>
                  <button
                    style={{
                      ...s.smallBtn,
                      borderColor: t("border", "#e5e7eb"),
                      color: t("destructive", "#ef4444"),
                      marginTop: "0.25rem",
                    }}
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
              <label
                style={{
                  ...s.assetCard,
                  ...s.dashed,
                  borderColor: t("border", "#e5e7eb"),
                  cursor: "pointer",
                }}
              >
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
